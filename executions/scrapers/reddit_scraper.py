"""
Scraper para Reddit usando a interface JSON pública (sem API key).
Coleta top posts da semana de cada subreddit configurado.
Usa fallback entre domínios: www -> old -> fallback HTML.
"""

import logging
import time
import requests
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import REDDIT_SUBREDDITS, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES
from executions.scrapers.base_scraper import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Domínios em ordem de preferência para o endpoint .json
REDDIT_DOMAINS = [
    "https://www.reddit.com",
    "https://old.reddit.com",
]


class RedditScraper(BaseScraper):
    """Scraper para subreddits configurados via JSON público do Reddit."""

    def __init__(self):
        super().__init__()
        # Headers que imitam navegador real - evita bloqueio 403
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })
        self._working_domain: Optional[str] = None

    def _reddit_json(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Faz GET em /{path}.json com fallback entre domínios.
        Garante que não há barra dupla na URL.
        """
        path = path.strip("/")  # remove barras extras

        # Se já descobrimos um domínio funcional, tenta ele primeiro
        domains = list(REDDIT_DOMAINS)
        if self._working_domain:
            domains.remove(self._working_domain)
            domains.insert(0, self._working_domain)

        for domain in domains:
            url = f"{domain}/{path}"
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    logger.info(f"[Reddit][{domain}] Tentativa {attempt} GET {url}")
                    response = self.session.get(
                        url, params=params, timeout=REQUEST_TIMEOUT
                    )

                    if response.status_code == 200:
                        data = response.json()
                        self._working_domain = domain
                        time.sleep(REQUEST_DELAY)
                        return data

                    # 429 = rate limit → espera curta e tenta próximo domínio
                    if response.status_code == 429:
                        wait = min(REQUEST_DELAY * attempt * 2, 3)
                        logger.warning(f"  Rate limited. Aguardando {wait}s...")
                        time.sleep(wait)
                        break  # tenta próximo domínio em vez de insistir

                    # 403/500 → tenta próximo domínio direto
                    if response.status_code in (403, 500, 502, 503):
                        logger.warning(
                            f"  HTTP {response.status_code} em {domain}. "
                            f"Tentando próximo domínio..."
                        )
                        break  # sai do retry, vai pro próximo domínio

                    # Outros erros → retry
                    response.raise_for_status()

                except requests.exceptions.JSONDecodeError:
                    logger.warning(f"  Resposta não é JSON válido de {url}")
                    break  # próximo domínio
                except requests.RequestException as e:
                    logger.warning(f"  Erro de rede: {e}")
                    if attempt < MAX_RETRIES:
                        time.sleep(REQUEST_DELAY * attempt)

        logger.error(f"Falha em todos os domínios para /{path}")
        return None

    def scrape(self) -> list[ScrapedItem]:
        """Coleta posts de todos os subreddits configurados."""
        all_items = []
        for sub_config in REDDIT_SUBREDDITS:
            logger.info(f"Scraping subreddit: {sub_config['name']}")
            try:
                items = self._scrape_subreddit(sub_config)
                all_items.extend(items)
                logger.info(
                    f"  -> {len(items)} posts coletados de {sub_config['name']}"
                )
            except Exception as e:
                logger.error(f"Erro ao scraper {sub_config['name']}: {e}")
        return all_items

    def _scrape_subreddit(self, sub_config: dict) -> list[ScrapedItem]:
        """Coleta posts de um subreddit específico."""
        name = sub_config["name"]
        max_posts = sub_config["max_posts"]
        search_terms = sub_config.get("search_terms")

        if search_terms:
            return self._search_subreddit(name, search_terms, max_posts)
        else:
            return self._get_top_posts(name, max_posts)

    def _get_top_posts(self, subreddit_name: str, max_posts: int) -> list[ScrapedItem]:
        """Busca top posts da semana de um subreddit."""
        sub = subreddit_name.replace("r/", "")
        data = self._reddit_json(
            f"r/{sub}/top.json",
            params={"t": "week", "limit": max_posts, "raw_json": 1},
        )
        if not data:
            return []
        return self._parse_listing(data, subreddit_name)

    def _search_subreddit(
        self, subreddit_name: str, search_terms: list[str], max_posts: int
    ) -> list[ScrapedItem]:
        """Busca posts por termos específicos dentro de um subreddit."""
        sub = subreddit_name.replace("r/", "")
        all_items = []
        seen_ids = set()

        per_term_limit = max(2, max_posts // len(search_terms))

        for term in search_terms:
            data = self._reddit_json(
                f"r/{sub}/search.json",
                params={
                    "q": term,
                    "restrict_sr": "on",
                    "sort": "relevance",
                    "t": "week",
                    "limit": per_term_limit,
                    "raw_json": 1,
                },
            )
            if not data:
                continue

            items = self._parse_listing(data, subreddit_name)
            for item in items:
                if item.url not in seen_ids:
                    seen_ids.add(item.url)
                    item.tags.append(f"busca:{term}")
                    all_items.append(item)

        all_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_items[:max_posts]

    def _parse_listing(self, data: dict, subreddit_name: str) -> list[ScrapedItem]:
        """Converte um listing do Reddit em lista de ScrapedItem."""
        items = []

        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            if not post:
                continue

            if post.get("removed_by_category") or post.get("is_robot_indexable") is False:
                continue

            title = post.get("title", "").strip()
            if not title:
                continue

            selftext = post.get("selftext", "")[:500]
            if not selftext:
                selftext = title

            permalink = post.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}" if permalink else ""

            external_url = post.get("url", "")
            if external_url and "reddit.com" not in external_url:
                selftext = f"{selftext}\n\nLink: {external_url}" if selftext else external_url

            author = post.get("author", "desconhecido")
            score = post.get("score", 0)
            num_comments = post.get("num_comments", 0)

            items.append(
                ScrapedItem(
                    title=title,
                    source="Reddit",
                    channel=subreddit_name,
                    description=selftext.strip(),
                    author=f"u/{author}",
                    url=post_url,
                    relevance_score=score + (num_comments * 2),
                    tags=["reddit", "ia", "tecnologia"],
                )
            )

        return items
