"""
Scraper para newsletters hospedadas no beehiiv:
The Neuron Daily, TechDrop News, The Rundown AI.

Estratégias de extração (beehiiv renderiza via JavaScript):
1. Remix JSON: extrai dados de window.__remixContext no /archive (Neuron Daily)
2. Sitemap + JSON-LD: busca URLs recentes no sitemap.xml e extrai metadados
   estruturados de cada página de artigo (TechDrop, Rundown AI, fallback geral)
"""

import json
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import NEWSLETTERS
from executions.scrapers.base_scraper import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)


class NewsletterScraper(BaseScraper):
    """Scraper para newsletters beehiiv."""

    def scrape(self) -> list[ScrapedItem]:
        """Coleta artigos de todas as newsletters em paralelo."""
        all_items = []

        def _scrape_one(newsletter):
            try:
                items = self._scrape_newsletter(newsletter)
                logger.info(f"  -> {len(items)} artigos de {newsletter['name']}")
                return items
            except Exception as e:
                logger.error(f"Erro ao scraper {newsletter['name']}: {e}")
                return []

        with ThreadPoolExecutor(max_workers=len(NEWSLETTERS)) as pool:
            futures = {pool.submit(_scrape_one, nl): nl for nl in NEWSLETTERS}
            for future in as_completed(futures):
                all_items.extend(future.result())

        return all_items

    def _scrape_newsletter(self, newsletter: dict) -> list[ScrapedItem]:
        """Tenta múltiplas estratégias para extrair artigos."""
        name = newsletter["name"]
        url = newsletter["url"]
        max_articles = newsletter["max_articles"]

        # Estratégia 1: Remix JSON (funciona no Neuron Daily)
        items = self._scrape_via_remix_json(name, url, max_articles)
        if items:
            return items

        # Estratégia 2: Sitemap + JSON-LD (funciona em todos os beehiiv)
        items = self._scrape_via_sitemap(name, url, max_articles)
        if items:
            return items

        logger.warning(f"  Nenhuma estratégia funcionou para {name}")
        return []

    # ==================================================================
    # ESTRATÉGIA 1: Remix JSON (window.__remixContext no /archive)
    # ==================================================================

    def _scrape_via_remix_json(
        self, name: str, base_url: str, max_articles: int
    ) -> list[ScrapedItem]:
        """Extrai artigos do JSON embutido no __remixContext da página /archive."""
        archive_url = base_url.rstrip("/") + "/archive?page=1"
        html = self.fetch_page(archive_url)
        if not html:
            return []

        # Procura o JSON do Remix no HTML
        match = re.search(
            r"window\.__remixContext\s*=\s*(\{.*?\});\s*</script>",
            html,
            re.DOTALL,
        )
        if not match:
            logger.debug(f"  __remixContext não encontrado para {name}")
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.debug(f"  JSON inválido no __remixContext de {name}")
            return []

        # Navega até o array de posts
        posts = self._extract_posts_from_remix(data)
        if not posts:
            logger.debug(f"  Nenhum post encontrado no __remixContext de {name}")
            return []

        logger.info(f"  Remix JSON: {len(posts)} posts encontrados para {name}")

        items = []
        for post in posts[:max_articles]:
            title = post.get("web_title", "").strip()
            if not title:
                continue

            slug = post.get("parameterized_web_title", "")
            post_url = f"{base_url.rstrip('/')}/p/{slug}" if slug else base_url

            subtitle = post.get("web_subtitle", "")
            authors = post.get("authors", [])
            author_name = authors[0].get("name", name) if authors else name
            published_date = post.get("publish_date", "") or post.get("created_at", "")

            items.append(
                ScrapedItem(
                    title=title,
                    source="Newsletter",
                    channel=name,
                    description=subtitle,
                    author=author_name,
                    url=post_url,
                    tags=["newsletter", "ia", "tecnologia"],
                    published_date=published_date,
                    comment_count=0,
                )
            )

        return items

    def _extract_posts_from_remix(self, data: dict) -> list[dict]:
        """Navega na estrutura do __remixContext para encontrar o array de posts."""
        loader_data = data.get("state", {}).get("loaderData", {})
        for _key, value in loader_data.items():
            if isinstance(value, dict) and "paginatedPosts" in value:
                return value["paginatedPosts"].get("posts", [])
        return []

    # ==================================================================
    # ESTRATÉGIA 2: Sitemap + JSON-LD (universal para beehiiv)
    # ==================================================================

    def _scrape_via_sitemap(
        self, name: str, base_url: str, max_articles: int
    ) -> list[ScrapedItem]:
        """Busca URLs de artigos no sitemap.xml e extrai JSON-LD de cada página."""
        sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
        xml_text = self.fetch_page(sitemap_url)
        if not xml_text:
            return []

        # Parse do sitemap XML
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.debug(f"  Sitemap XML inválido para {name}")
            return []

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Extrai URLs de artigos (contêm /p/)
        article_entries = []
        for url_el in root.findall(".//sm:url", ns):
            loc = url_el.find("sm:loc", ns)
            if loc is None or "/p/" not in loc.text:
                continue
            lastmod_el = url_el.find("sm:lastmod", ns)
            lastmod = lastmod_el.text if lastmod_el is not None else ""
            article_entries.append((loc.text, lastmod))

        if not article_entries:
            logger.debug(f"  Nenhum artigo encontrado no sitemap de {name}")
            return []

        # Ordena por data mais recente
        article_entries.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            f"  Sitemap: {len(article_entries)} artigos totais, "
            f"buscando top {max_articles} mais recentes"
        )

        # Busca JSON-LD de artigos recentes em paralelo
        candidates = [url for url, _ in article_entries[:max_articles * 2]]

        items = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            future_map = {
                pool.submit(self.fetch_page, url): url for url in candidates
            }
            for future in as_completed(future_map):
                if len(items) >= max_articles:
                    break
                url = future_map[future]
                html = future.result()
                if not html:
                    continue
                item = self._parse_jsonld_article(html, name, url)
                if item:
                    items.append(item)

        return items

    def _parse_jsonld_article(
        self, html: str, source_name: str, url: str
    ) -> ScrapedItem | None:
        """Extrai dados de um artigo via JSON-LD (schema.org)."""
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", type="application/ld+json")
        if not script or not script.string:
            return None

        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            return None

        # Aceita apenas tipo Article
        if data.get("@type") != "Article":
            return None

        title = data.get("headline", "").strip()
        if not title or len(title) < 5:
            return None

        description = data.get("description", "")
        published_date = data.get("datePublished", "") or data.get("dateModified", "")
        author_data = data.get("author", {})
        if isinstance(author_data, dict):
            author = author_data.get("name", source_name)
        elif isinstance(author_data, list) and author_data:
            author = author_data[0].get("name", source_name)
        else:
            author = source_name

        return ScrapedItem(
            title=title,
            source="Newsletter",
            channel=source_name,
            description=description,
            author=author,
            url=url,
            tags=["newsletter", "ia", "tecnologia"],
            published_date=published_date,
            comment_count=0,
        )
