"""
Scraper para YouTube usando RSS Feeds dos canais.
Busca vídeos recentes, prioriza por data de lançamento e relevância (keywords).
RSS é muito mais rápido que yt-dlp (~0.3s por canal vs ~5-10s).

Score = (keyword_matches × 15) + recency_bonus (0-20 pts baseado na idade do vídeo)
Garante pelo menos YOUTUBE_MAX_RESULTS vídeos, preenchendo com recentes se necessário.
"""

import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import YOUTUBE_CHANNELS, YOUTUBE_KEYWORDS, YOUTUBE_MAX_RESULTS
from executions.scrapers.base_scraper import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Namespaces do Atom feed do YouTube
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


class YouTubeScraper(BaseScraper):
    """Scraper para canais do YouTube via RSS feeds."""

    def __init__(self):
        super().__init__()
        self._channel_id_cache: dict[str, str] = {}

    def scrape(self) -> list[ScrapedItem]:
        """Coleta vídeos de todos os canais em paralelo e filtra por keywords."""
        all_items = []

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(self._scrape_channel, ch): ch
                for ch in YOUTUBE_CHANNELS
            }
            for future in as_completed(futures):
                ch = futures[future]
                try:
                    items = future.result()
                    all_items.extend(items)
                    logger.info(f"  -> {len(items)} vídeos de {ch['name']}")
                except Exception as e:
                    logger.error(f"Erro ao scraper YouTube {ch['name']}: {e}")

        # Ordena por score e limita a 3 vídeos por canal
        all_items.sort(key=lambda x: x.relevance_score, reverse=True)
        channel_count: dict[str, int] = {}
        result = []
        for item in all_items:
            count = channel_count.get(item.channel, 0)
            if count >= 3:
                continue
            channel_count[item.channel] = count + 1
            result.append(item)
            if len(result) >= YOUTUBE_MAX_RESULTS:
                break
        return result

    def _scrape_channel(self, channel: dict) -> list[ScrapedItem]:
        """Scrape um canal: resolve ID → fetch RSS → filtra por keywords."""
        handle = channel["handle"]
        name = channel["name"]

        channel_id = self._resolve_channel_id(handle)
        if not channel_id:
            logger.warning(f"  Não conseguiu resolver channel_id para @{handle}")
            return []

        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        xml_text = self.fetch_page(feed_url)
        if not xml_text:
            return []

        return self._parse_feed(xml_text, name)

    def _resolve_channel_id(self, handle: str) -> Optional[str]:
        """Resolve @handle para channel_id buscando a página do canal."""
        if handle in self._channel_id_cache:
            return self._channel_id_cache[handle]

        url = f"https://www.youtube.com/@{handle}"
        html = self.fetch_page(url)
        if not html:
            return None

        # Tenta extrair channel_id de várias formas
        patterns = [
            r'"externalId"\s*:\s*"(UC[^"]+)"',
            r'"channelId"\s*:\s*"(UC[^"]+)"',
            r'<meta\s+itemprop="identifier"\s+content="(UC[^"]+)"',
            r'<link\s+rel="canonical"\s+href="https://www\.youtube\.com/channel/(UC[^"]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                cid = match.group(1)
                self._channel_id_cache[handle] = cid
                logger.info(f"  Channel ID para @{handle}: {cid}")
                return cid

        logger.warning(f"  Channel ID não encontrado para @{handle}")
        return None

    @staticmethod
    def _recency_bonus(published_str: str) -> float:
        """Calcula bônus de recência: quanto mais recente, maior o score."""
        try:
            pub = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - pub).days
        except (ValueError, TypeError):
            return 0

        if age_days <= 3:
            return 20
        if age_days <= 7:
            return 15
        if age_days <= 14:
            return 10
        if age_days <= 30:
            return 5
        return 0

    def _parse_feed(self, xml_text: str, channel_name: str) -> list[ScrapedItem]:
        """Parse do Atom feed. Retorna todos os vídeos com score composto."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning(f"  XML inválido no feed de {channel_name}")
            return []

        items = []
        keywords_lower = [kw.lower() for kw in YOUTUBE_KEYWORDS]

        for entry in root.findall("atom:entry", NS):
            title_el = entry.find("atom:title", NS)
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            if not title:
                continue

            # Video URL
            link_el = entry.find("atom:link[@rel='alternate']", NS)
            video_url = link_el.get("href", "") if link_el is not None else ""

            # Published date
            pub_el = entry.find("atom:published", NS)
            published = pub_el.text if pub_el is not None and pub_el.text else ""

            # Description
            media_group = entry.find("media:group", NS)
            description = ""
            if media_group is not None:
                desc_el = media_group.find("media:description", NS)
                description = (desc_el.text or "")[:500] if desc_el is not None else ""

            # Keywords match
            text_lower = f"{title} {description}".lower()
            matched_keywords = [kw for kw in keywords_lower if kw in text_lower]

            # Score composto: relevância (keywords) + recência
            keyword_score = len(matched_keywords) * 15
            recency = self._recency_bonus(published)
            score = keyword_score + recency

            # Author
            author_el = entry.find("atom:author/atom:name", NS)
            author = author_el.text if author_el is not None and author_el.text else channel_name

            tags = ["youtube"]
            if matched_keywords:
                tags += matched_keywords[:5]

            items.append(
                ScrapedItem(
                    title=title,
                    source="YouTube",
                    channel=channel_name,
                    description=description.strip(),
                    author=author,
                    url=video_url,
                    relevance_score=score,
                    tags=tags,
                )
            )

        return items
