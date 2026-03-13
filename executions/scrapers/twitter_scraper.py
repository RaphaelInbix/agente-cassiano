"""
Scraper de X/Twitter via instâncias Nitter + Claude Vision.
Busca tweets públicos de perfis configurados e usa Claude para
extrair conteúdo relevante sobre IA e negócios.
"""

import json
import logging
import re
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from executions.scrapers.base_scraper import BaseScraper, ScrapedItem
from config.settings import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    TWITTER_PROFILES,
    TWITTER_MAX_ITEMS,
    NITTER_INSTANCES,
)

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Analise o HTML abaixo de uma página de perfil do Twitter/X (via Nitter).
Extraia os tweets mais recentes que sejam relevantes para profissionais de negócios interessados em IA.

Retorne APENAS um JSON array (sem markdown) com os tweets encontrados, no formato:
[
  {
    "text": "Texto completo do tweet",
    "date": "YYYY-MM-DD",
    "url_path": "/username/status/123456789",
    "is_retweet": false
  }
]

Regras:
- Inclua apenas tweets sobre IA, tecnologia, negócios, produtividade ou ferramentas
- Ignore tweets pessoais, memes, ou sem relação com IA/negócios
- Máximo 5 tweets por perfil
- Se não encontrar tweets relevantes, retorne []
- O campo url_path deve ser o path relativo do tweet (ex: /username/status/123)"""


class TwitterScraper(BaseScraper):
    """Coleta tweets de perfis públicos via Nitter + Claude Vision."""

    def __init__(self):
        super().__init__()
        self._client = None

    def _get_client(self):
        """Lazy-load do cliente Anthropic."""
        if self._client is None and ANTHROPIC_API_KEY:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except Exception as e:
                logger.error(f"Erro ao inicializar cliente Anthropic: {e}")
        return self._client

    def scrape(self) -> list[ScrapedItem]:
        """Coleta tweets de todos os perfis configurados."""
        client = self._get_client()
        if not client:
            logger.error("Twitter scraper requer ANTHROPIC_API_KEY configurada")
            return []

        all_items = []

        for profile in TWITTER_PROFILES:
            try:
                items = self._scrape_profile(client, profile)
                all_items.extend(items)
                logger.info(
                    f"  @{profile['handle']}: {len(items)} tweets relevantes"
                )
            except Exception as e:
                logger.error(
                    f"  Erro ao coletar @{profile['handle']}: {e}"
                )

        # Limita total de tweets
        all_items = all_items[:TWITTER_MAX_ITEMS]
        logger.info(f"Twitter: {len(all_items)} tweets coletados no total")
        return all_items

    def _scrape_profile(
        self, client, profile: dict
    ) -> list[ScrapedItem]:
        """Coleta tweets de um perfil específico via Nitter."""
        handle = profile["handle"]
        name = profile["name"]

        # Tenta cada instância Nitter até conseguir
        html = None
        for instance in NITTER_INSTANCES:
            url = f"{instance}/{handle}"
            html = self.fetch_page(url)
            if html and len(html) > 1000:
                logger.debug(f"  Nitter OK: {instance}/{handle}")
                break
            html = None

        if not html:
            logger.warning(f"  Nenhuma instância Nitter respondeu para @{handle}")
            return []

        # Trunca HTML para economizar tokens (pega só o corpo principal)
        html_trimmed = self._trim_html(html)

        # Usa Claude para extrair tweets relevantes do HTML
        tweets = self._extract_tweets_with_claude(client, html_trimmed, handle)

        # Converte para ScrapedItem
        items = []
        for tweet in tweets:
            tweet_url = f"https://x.com{tweet.get('url_path', f'/{handle}')}"
            text = tweet.get("text", "")

            items.append(ScrapedItem(
                title=text[:120] + ("..." if len(text) > 120 else ""),
                source="Twitter",
                channel=f"@{handle}",
                description=text,
                author=name,
                url=tweet_url,
                relevance_score=0.0,
                tags=["twitter", "ia"],
                published_date=tweet.get("date", datetime.now().strftime("%Y-%m-%d")),
                comment_count=0,
            ))

        return items

    def _extract_tweets_with_claude(
        self, client, html: str, handle: str
    ) -> list[dict]:
        """Usa Claude para extrair tweets relevantes do HTML Nitter."""
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                system=EXTRACTION_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Perfil: @{handle}\n\nHTML da página:\n{html}",
                }],
            )

            response_text = response.content[0].text.strip()
            # Remove possível markdown wrapping
            if response_text.startswith("```"):
                response_text = re.sub(r"^```\w*\n?", "", response_text)
                response_text = re.sub(r"\n?```$", "", response_text)

            tweets = json.loads(response_text)
            if not isinstance(tweets, list):
                return []
            return tweets

        except Exception as e:
            logger.error(f"  Erro Claude ao extrair tweets de @{handle}: {e}")
            return []

    def _trim_html(self, html: str) -> str:
        """Reduz HTML para economizar tokens. Mantém apenas conteúdo de tweets."""
        # Remove head, scripts, styles
        html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL)
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        html = re.sub(r"<nav[^>]*>.*?</nav>", "", html, flags=re.DOTALL)
        html = re.sub(r"<footer[^>]*>.*?</footer>", "", html, flags=re.DOTALL)
        # Remove comentários HTML
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
        # Compacta whitespace
        html = re.sub(r"\s+", " ", html)

        # Limita tamanho (Claude tem limite de contexto, e queremos economizar tokens)
        max_chars = 15000
        if len(html) > max_chars:
            html = html[:max_chars]

        return html
