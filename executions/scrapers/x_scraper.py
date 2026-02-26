"""
Scraper para X (Twitter) via web scraping.
Usa múltiplas estratégias com fallback:
1. Nitter/xcancel (frontends alternativos open-source)
2. RSS bridges públicos
3. Twitter syndication embeds
"""

import logging
import re
import time
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import X_PROFILES, X_HASHTAGS, REQUEST_DELAY
from executions.scrapers.base_scraper import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Instâncias Nitter/alternativas atualizadas (ordem de prioridade)
NITTER_INSTANCES = [
    "https://xcancel.com",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.woodland.cafe",
    "https://nitter.1d4.us",
    "https://nitter.net",
]


class XScraper(BaseScraper):
    """Scraper para perfis e hashtags do X via frontends alternativos."""

    def __init__(self):
        super().__init__()
        self.working_instance = None
        # Headers mais robustos para evitar bloqueios
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        })

    def scrape(self) -> list[ScrapedItem]:
        """Coleta tweets dos perfis e hashtags configurados."""
        all_items = []

        # Tenta encontrar instância funcionando
        self._find_working_instance()

        if self.working_instance:
            # Scrape via Nitter/xcancel
            all_items = self._scrape_via_nitter()
        else:
            logger.warning(
                "Nenhuma instância Nitter/xcancel disponível. "
                "Tentando fallback via RSS bridge..."
            )

        # Se Nitter não retornou nada, tenta RSS bridge
        if not all_items:
            logger.info("Tentando coleta via RSS bridge...")
            all_items = self._scrape_via_rss_bridge()

        # Se RSS bridge também falhou, tenta syndication
        if not all_items:
            logger.info("Tentando coleta via Twitter syndication...")
            all_items = self._scrape_via_syndication()

        if not all_items:
            logger.error(
                "Todas as estratégias de scraping do X falharam. "
                "Nenhum tweet coletado."
            )

        return all_items

    def _fetch_page_no_retry_on_block(self, url: str) -> str | None:
        """Fetch que não faz retry em 403/401 (bloqueio, não erro transitório)."""
        try:
            logger.info(f"[X] GET {url}")
            response = self.session.get(url, timeout=REQUEST_DELAY + 8)
            if response.status_code in (403, 401, 429):
                logger.debug(f"  Bloqueado ({response.status_code}): {url}")
                return None
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return response.text
        except Exception as e:
            logger.debug(f"  Erro: {e}")
            return None

    def _find_working_instance(self):
        """Testa instâncias Nitter com um perfil real (não só a homepage)."""
        # Perfil de teste: elonmusk (alto tráfego, maior chance de cache)
        test_username = "elonmusk"

        for instance in NITTER_INSTANCES:
            try:
                logger.info(f"Testando instância: {instance}/{test_username}")
                response = self.session.get(
                    f"{instance}/{test_username}",
                    timeout=12,
                    allow_redirects=True,
                )
                if response.status_code == 200:
                    html_lower = response.text.lower()
                    # Verifica se retornou conteúdo real de timeline
                    if any(marker in html_lower for marker in [
                        "timeline-item", "tweet", "status",
                        "tweet-content", "pinned",
                    ]):
                        self.working_instance = instance
                        logger.info(f"Instância funcional (perfil OK): {instance}")
                        time.sleep(REQUEST_DELAY)
                        return
                    else:
                        logger.debug(f"  {instance} respondeu mas sem tweets no HTML")
                else:
                    logger.debug(f"  {instance} retornou HTTP {response.status_code}")
            except Exception as e:
                logger.debug(f"  {instance} falhou: {e}")
                continue

        logger.warning("Nenhuma instância Nitter/xcancel respondeu com perfil real.")

    # ==================================================================
    # ESTRATÉGIA 1: Nitter / xcancel
    # ==================================================================

    def _scrape_via_nitter(self) -> list[ScrapedItem]:
        """Coleta tweets via instância Nitter/xcancel funcional."""
        all_items = []
        consecutive_failures = 0
        max_consecutive_failures = 3  # Desiste se 3 seguidos falharem

        # Scrape perfis
        for profile in X_PROFILES:
            if consecutive_failures >= max_consecutive_failures:
                logger.warning(
                    f"  {consecutive_failures} falhas consecutivas. "
                    f"Instância provavelmente bloqueando. Abortando Nitter."
                )
                break

            logger.info(f"Scraping perfil X: {profile}")
            try:
                items = self._scrape_nitter_profile(profile)
                all_items.extend(items)
                logger.info(f"  -> {len(items)} tweets de {profile}")
                if items:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
            except Exception as e:
                logger.error(f"Erro ao scraper perfil {profile}: {e}")
                consecutive_failures += 1
            time.sleep(REQUEST_DELAY)

        # Scrape hashtags (só se perfis não abortaram)
        if consecutive_failures < max_consecutive_failures:
            for hashtag in X_HASHTAGS:
                if consecutive_failures >= max_consecutive_failures:
                    break
                logger.info(f"Scraping hashtag X: {hashtag}")
                try:
                    items = self._scrape_nitter_hashtag(hashtag)
                    all_items.extend(items)
                    logger.info(f"  -> {len(items)} tweets de {hashtag}")
                    if items:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                except Exception as e:
                    logger.error(f"Erro ao scraper hashtag {hashtag}: {e}")
                    consecutive_failures += 1
                time.sleep(REQUEST_DELAY)

        return all_items

    def _scrape_nitter_profile(self, handle: str, max_tweets: int = 5) -> list[ScrapedItem]:
        """Coleta tweets recentes de um perfil via Nitter."""
        username = handle.replace("@", "")
        url = f"{self.working_instance}/{username}"
        html = self._fetch_page_no_retry_on_block(url)
        if not html:
            return []

        return self._parse_nitter_html(html, handle, username, max_tweets)

    def _scrape_nitter_hashtag(self, hashtag: str, max_tweets: int = 5) -> list[ScrapedItem]:
        """Coleta tweets de uma hashtag via Nitter."""
        tag = hashtag.replace("#", "")
        url = f"{self.working_instance}/search?q=%23{tag}&f=tweets"
        html = self._fetch_page_no_retry_on_block(url)
        if not html:
            return []

        return self._parse_nitter_html(html, hashtag, tag, max_tweets)

    def _parse_nitter_html(
        self, html: str, source_label: str, username: str, max_tweets: int
    ) -> list[ScrapedItem]:
        """Extrai tweets do HTML de uma página Nitter/xcancel."""
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # Seletores em ordem de prioridade (variam entre instâncias)
        tweet_selectors = [
            ".timeline-item",
            ".tweet-body",
            ".status",
            "article",
            '[class*="tweet"]',
            '[class*="status"]',
        ]

        tweets = []
        for selector in tweet_selectors:
            found = soup.select(selector)
            # Filtra elementos muito pequenos (navegação, etc.)
            found = [el for el in found if len(el.get_text(strip=True)) > 20]
            if found:
                tweets = found
                break

        if not tweets:
            logger.debug(f"  Nenhum tweet encontrado no HTML para {source_label}")
            return []

        for tweet_el in tweets[:max_tweets]:
            item = self._parse_nitter_tweet(tweet_el, source_label, username)
            if item:
                items.append(item)

        return items

    def _parse_nitter_tweet(
        self, element, source_label: str, username: str
    ) -> ScrapedItem | None:
        """Extrai dados de um tweet do HTML do Nitter/xcancel."""
        # Texto do tweet - múltiplos seletores para compatibilidade
        content_el = element.select_one(
            ".tweet-content, .status-content, .tweet-text, "
            ".media-body, [class*='content']"
        )
        if not content_el:
            # Fallback: tenta qualquer <p> dentro do elemento
            content_el = element.find("p")
        if not content_el:
            return None

        text = content_el.get_text(strip=True)
        if not text or len(text) < 10:
            return None

        # Título = primeiros 120 chars do tweet
        title = text[:120] + ("..." if len(text) > 120 else "")

        # Link do tweet - tenta múltiplos seletores
        tweet_url = self._extract_tweet_url(element, username)

        # Autor
        author_el = element.select_one(
            ".username, .tweet-header a, .fullname, "
            "[class*='user'], [class*='author']"
        )
        author = author_el.get_text(strip=True) if author_el else source_label

        # Stats para relevância (likes, retweets, replies)
        score = self._extract_tweet_stats(element)

        return ScrapedItem(
            title=title,
            source="X (Twitter)",
            channel=source_label,
            description=text,
            author=author,
            url=tweet_url,
            relevance_score=score,
            tags=["twitter", "ia", "tecnologia"],
        )

    def _extract_tweet_url(self, element, username: str) -> str:
        """Extrai a URL do tweet do HTML, com múltiplos fallbacks."""
        # Tenta seletores específicos
        link_selectors = [
            ".tweet-link",
            "a[href*='/status/']",
            ".tweet-date a",
            ".status-link",
            "a[href*='/i/']",
        ]

        for selector in link_selectors:
            link_el = element.select_one(selector)
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if href.startswith("/"):
                    return f"https://x.com{href}"
                if "status/" in href:
                    # Normaliza para x.com
                    match = re.search(r"(\w+)/status/(\d+)", href)
                    if match:
                        return f"https://x.com/{match.group(1)}/status/{match.group(2)}"
                return href

        # Fallback: qualquer link que parece ser de tweet
        all_links = element.find_all("a", href=True)
        for link in all_links:
            href = link["href"]
            if "/status/" in href:
                if href.startswith("/"):
                    return f"https://x.com{href}"
                return href

        return f"https://x.com/{username}"

    def _extract_tweet_stats(self, element) -> int:
        """Extrai métricas de engajamento (likes, RTs, replies)."""
        score = 0

        # Seletores para stats do Nitter/xcancel
        stat_selectors = [
            ".tweet-stat",
            ".icon-container",
            "[class*='stat']",
            "[class*='count']",
        ]

        for selector in stat_selectors:
            stats = element.select(selector)
            if stats:
                for stat in stats:
                    nums = re.findall(r"[\d,]+", stat.get_text())
                    for num_str in nums:
                        try:
                            val = int(num_str.replace(",", ""))
                            score += val
                        except ValueError:
                            continue
                if score > 0:
                    break  # Já encontrou stats, não precisa tentar outros seletores

        return score

    # ==================================================================
    # ESTRATÉGIA 2: RSS Bridge
    # ==================================================================

    def _scrape_via_rss_bridge(self) -> list[ScrapedItem]:
        """Fallback: tenta coletar via RSS bridges públicos."""
        items = []

        rss_bridges = [
            "https://rss-bridge.org/bridge01",
            "https://rss-bridge.org/bridge02",
        ]

        for bridge_url in rss_bridges:
            if items:
                break  # Já conseguiu dados

            for profile in X_PROFILES:
                username = profile.replace("@", "")
                try:
                    url = (
                        f"{bridge_url}/?action=display&bridge=TwitterBridge"
                        f"&context=By+username&u={username}"
                        f"&norep=on&noretweet=on&format=Html"
                    )
                    logger.info(f"RSS Bridge: tentando {username} via {bridge_url}")
                    html = self.fetch_page(url)
                    if not html:
                        continue

                    soup = BeautifulSoup(html, "html.parser")

                    # RSS bridge retorna itens em <div class="feeditem"> ou <item>
                    feed_items = soup.select(
                        ".feeditem, .feed-item, item, entry, article, .rss-item"
                    )

                    for feed_item in feed_items[:5]:
                        title_el = feed_item.select_one(
                            ".itemtitle, .item-title, title, h2, h3, a"
                        )
                        content_el = feed_item.select_one(
                            ".itemcontent, .item-content, description, content, p"
                        )

                        text = ""
                        if content_el:
                            text = content_el.get_text(strip=True)
                        elif title_el:
                            text = title_el.get_text(strip=True)

                        if not text or len(text) < 10:
                            continue

                        # Tenta extrair URL do item
                        link_el = feed_item.select_one("a[href*='x.com'], a[href*='twitter.com']")
                        tweet_url = link_el["href"] if link_el else f"https://x.com/{username}"

                        items.append(
                            ScrapedItem(
                                title=text[:120] + ("..." if len(text) > 120 else ""),
                                source="X (Twitter)",
                                channel=profile,
                                description=text,
                                author=profile,
                                url=tweet_url,
                                relevance_score=0,
                                tags=["twitter", "ia", "tecnologia"],
                            )
                        )

                    if items:
                        logger.info(f"  RSS Bridge: {len(items)} tweets coletados")

                except Exception as e:
                    logger.debug(f"  RSS Bridge falhou para {username}: {e}")
                    continue

                time.sleep(REQUEST_DELAY)

        return items

    # ==================================================================
    # ESTRATÉGIA 3: Twitter Syndication (embed)
    # ==================================================================

    def _scrape_via_syndication(self) -> list[ScrapedItem]:
        """Último fallback: tenta via Twitter syndication/embeds."""
        items = []

        for profile in X_PROFILES:
            username = profile.replace("@", "")

            # Tenta endpoint de syndication
            syndication_urls = [
                f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}",
                f"https://syndication.x.com/srv/timeline-profile/screen-name/{username}",
            ]

            for url in syndication_urls:
                try:
                    logger.info(f"Syndication: tentando {username}")
                    html = self.fetch_page(url)
                    if not html:
                        continue

                    soup = BeautifulSoup(html, "html.parser")

                    tweet_divs = soup.select(
                        '[data-tweet-id], .timeline-Tweet, .tweet, article, '
                        '[class*="Tweet"], [class*="tweet"]'
                    )

                    for tweet_div in tweet_divs[:5]:
                        text_el = tweet_div.select_one(
                            ".timeline-Tweet-text, .tweet-text, p, "
                            "[class*='text'], [class*='content']"
                        )
                        if not text_el:
                            continue
                        text = text_el.get_text(strip=True)
                        if len(text) < 10:
                            continue

                        tweet_id = tweet_div.get("data-tweet-id", "")
                        tweet_url = (
                            f"https://x.com/{username}/status/{tweet_id}"
                            if tweet_id
                            else f"https://x.com/{username}"
                        )

                        items.append(
                            ScrapedItem(
                                title=text[:120] + ("..." if len(text) > 120 else ""),
                                source="X (Twitter)",
                                channel=profile,
                                description=text,
                                author=profile,
                                url=tweet_url,
                                relevance_score=0,
                                tags=["twitter", "ia", "tecnologia"],
                            )
                        )

                    if items:
                        break  # Encontrou um endpoint funcional

                except Exception as e:
                    logger.debug(f"  Syndication falhou para {username}: {e}")
                    continue

            time.sleep(REQUEST_DELAY)

        return items
