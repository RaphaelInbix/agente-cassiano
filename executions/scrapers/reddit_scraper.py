"""
Scraper para Reddit usando OAuth API (recomendado para servidores).
Fallback para JSON público quando não há credenciais configuradas.

OAuth é essencial para deploy em cloud (Render, etc.) porque o Reddit
bloqueia/rate-limita agressivamente IPs de datacenter no endpoint público.
Com OAuth: 60 requests/min garantidos, sem bloqueio por IP.
"""

import logging
import time
import requests
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import (
    REDDIT_SUBREDDITS, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
)
from executions.scrapers.base_scraper import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Domínios para fallback (sem OAuth)
REDDIT_DOMAINS = [
    "https://www.reddit.com",
    "https://old.reddit.com",
]

OAUTH_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_BASE_URL = "https://oauth.reddit.com"


class RedditScraper(BaseScraper):
    """Scraper para subreddits via Reddit OAuth API (ou JSON público como fallback)."""

    def __init__(self):
        super().__init__()
        self._access_token: Optional[str] = None
        self._use_oauth = bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)
        self._working_domain: Optional[str] = None

        # Headers para ambos os modos
        self.session.headers.update({
            "User-Agent": (
                "AgenteCassiano/1.0 (by /u/InbixBot) "
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        })

        if self._use_oauth:
            self._authenticate()

    def _authenticate(self):
        """Obtém access_token via OAuth2 client_credentials."""
        try:
            response = requests.post(
                OAUTH_TOKEN_URL,
                auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                headers={
                    "User-Agent": "AgenteCassiano/1.0 (by /u/InbixBot)",
                },
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                if self._access_token:
                    self.session.headers["Authorization"] = f"Bearer {self._access_token}"
                    logger.info("Reddit OAuth autenticado com sucesso")
                    return
            logger.warning(
                f"Falha na autenticação OAuth: {response.status_code} - "
                f"{response.text[:200]}. Usando fallback público."
            )
            self._use_oauth = False
        except requests.RequestException as e:
            logger.warning(f"Erro na autenticação OAuth: {e}. Usando fallback público.")
            self._use_oauth = False

    def _reddit_get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        """Faz GET na API do Reddit (OAuth ou público com fallback)."""
        path = path.strip("/")

        if self._use_oauth:
            return self._oauth_get(path, params)
        return self._public_get(path, params)

    def _oauth_get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        """GET via OAuth API (oauth.reddit.com). Rate limit: 60 req/min."""
        url = f"{OAUTH_BASE_URL}/{path}"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)

                if response.status_code == 200:
                    time.sleep(REQUEST_DELAY)
                    return response.json()

                if response.status_code == 401:
                    logger.warning("Token expirado, re-autenticando...")
                    self._authenticate()
                    if not self._use_oauth:
                        return self._public_get(path, params)
                    continue

                if response.status_code == 429:
                    wait = min(REQUEST_DELAY * attempt * 2, 5)
                    logger.warning(f"  OAuth rate limited. Aguardando {wait}s...")
                    time.sleep(wait)
                    continue

                logger.warning(f"  OAuth HTTP {response.status_code} para {path}")
                if attempt < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY * attempt)

            except requests.RequestException as e:
                logger.warning(f"  OAuth erro de rede: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY * attempt)

        logger.error(f"OAuth falhou para /{path}. Tentando fallback público...")
        return self._public_get(path, params)

    def _public_get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        """GET via endpoint público (.json) com fallback entre domínios."""
        # Garante que o path termina com .json para o endpoint público
        json_path = path if path.endswith(".json") else f"{path}.json"

        domains = list(REDDIT_DOMAINS)
        if self._working_domain:
            domains.remove(self._working_domain)
            domains.insert(0, self._working_domain)

        for domain in domains:
            url = f"{domain}/{json_path}"
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = self.session.get(
                        url, params=params, timeout=REQUEST_TIMEOUT
                    )

                    if response.status_code == 200:
                        data = response.json()
                        self._working_domain = domain
                        time.sleep(REQUEST_DELAY)
                        return data

                    if response.status_code == 429:
                        wait = min(REQUEST_DELAY * attempt * 2, 3)
                        logger.warning(f"  Rate limited. Aguardando {wait}s...")
                        time.sleep(wait)
                        break

                    if response.status_code in (403, 500, 502, 503):
                        logger.warning(
                            f"  HTTP {response.status_code} em {domain}. "
                            f"Tentando próximo domínio..."
                        )
                        break

                    response.raise_for_status()

                except requests.exceptions.JSONDecodeError:
                    logger.warning(f"  Resposta não é JSON válido de {url}")
                    break
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

        # OAuth usa path sem .json, público adiciona automaticamente
        data = self._reddit_get(
            f"r/{sub}/top",
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
            data = self._reddit_get(
                f"r/{sub}/search",
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
