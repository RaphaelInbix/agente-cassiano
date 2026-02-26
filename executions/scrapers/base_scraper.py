"""
Base scraper com funcionalidades compartilhadas entre todos os scrapers.
"""

import time
import logging
import requests
from dataclasses import dataclass, field
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES

logger = logging.getLogger(__name__)


@dataclass
class ScrapedItem:
    """Representa um item coletado (artigo, post, tweet)."""
    title: str
    source: str
    channel: str
    description: str
    author: str
    url: str
    relevance_score: float = 0.0
    tags: list = field(default_factory=list)


class BaseScraper:
    """Classe base para todos os scrapers."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_page(self, url: str, params: Optional[dict] = None) -> Optional[str]:
        """Faz requisição HTTP com retry e delay anti-ban."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"[Tentativa {attempt}] GET {url}")
                response = self.session.get(
                    url, params=params, timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                time.sleep(REQUEST_DELAY)
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Erro na tentativa {attempt} para {url}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY * attempt)
        logger.error(f"Falha após {MAX_RETRIES} tentativas para {url}")
        return None

    def fetch_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """Faz requisição HTTP esperando resposta JSON."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"[Tentativa {attempt}] GET JSON {url}")
                response = self.session.get(
                    url, params=params, timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                time.sleep(REQUEST_DELAY)
                return response.json()
            except requests.RequestException as e:
                logger.warning(f"Erro na tentativa {attempt} para {url}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY * attempt)
        logger.error(f"Falha após {MAX_RETRIES} tentativas para {url}")
        return None

    def scrape(self) -> list[ScrapedItem]:
        """Método a ser implementado por cada scraper específico."""
        raise NotImplementedError("Subclasses devem implementar scrape()")
