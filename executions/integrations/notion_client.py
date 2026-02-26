"""
Cliente para a API do Notion.
Salva os artigos curados como blocos toggle na página configurada.
"""

import logging
import requests
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import NOTION_TOKEN, NOTION_PAGE_ID, NOTION_API_VERSION, NOTION_BASE_URL
from executions.scrapers.base_scraper import ScrapedItem

logger = logging.getLogger(__name__)


class NotionClient:
    """Cliente para a API do Notion para publicação de conteúdo curado."""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION,
        }
        self.page_id = NOTION_PAGE_ID

    def publish(self, items: list[ScrapedItem]) -> bool:
        """Publica todos os itens curados na página do Notion."""
        logger.info(f"Publicando {len(items)} itens no Notion...")

        # Agrupa por fonte
        newsletters = [i for i in items if i.source != "Reddit" and i.source != "X (Twitter)"]
        reddit_posts = [i for i in items if i.source == "Reddit"]
        x_posts = [i for i in items if i.source == "X (Twitter)"]

        blocks = []

        # Header com data
        blocks.append(self._heading_block(
            f"Curadoria Semanal - {datetime.now().strftime('%d/%m/%Y')}",
            level=1,
        ))
        blocks.append(self._divider_block())

        # Seção Newsletters
        if newsletters:
            blocks.append(self._heading_block("Newsletters", level=2))
            for item in newsletters:
                blocks.append(self._toggle_block(item))

        # Seção Reddit
        if reddit_posts:
            blocks.append(self._heading_block("Reddit", level=2))
            for item in reddit_posts:
                blocks.append(self._toggle_block(item))

        # Seção X
        if x_posts:
            blocks.append(self._heading_block("X (Twitter)", level=2))
            for item in x_posts:
                blocks.append(self._toggle_block(item))

        # Notion limita a 100 blocos por request
        success = True
        for i in range(0, len(blocks), 100):
            batch = blocks[i : i + 100]
            if not self._append_blocks(batch):
                success = False

        if success:
            logger.info("Publicação no Notion concluída com sucesso!")
        else:
            logger.error("Houve erros na publicação no Notion.")

        return success

    def _append_blocks(self, blocks: list[dict]) -> bool:
        """Envia blocos para a API do Notion."""
        url = f"{NOTION_BASE_URL}/blocks/{self.page_id}/children"
        payload = {"children": blocks}

        try:
            response = requests.patch(url, json=payload, headers=self.headers)
            if response.status_code == 200:
                logger.info(f"  -> {len(blocks)} blocos adicionados com sucesso.")
                return True
            else:
                logger.error(
                    f"  Erro ao adicionar blocos: {response.status_code} - "
                    f"{response.text[:300]}"
                )
                return False
        except requests.RequestException as e:
            logger.error(f"  Erro de rede ao publicar no Notion: {e}")
            return False

    def _toggle_block(self, item: ScrapedItem) -> dict:
        """Cria um bloco toggle (details) para um item curado."""
        # Conteúdo interno do toggle
        children = []

        # Fonte e canal (cinza)
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Fonte: {item.source} | Canal: {item.channel}"},
                        "annotations": {"color": "gray"},
                    }
                ]
            },
        })

        # Descrição/resumo
        description = item.description[:2000] if item.description else "Sem descrição disponível."
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": description},
                    }
                ]
            },
        })

        # Autor (cinza)
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Autor: {item.author}"},
                        "annotations": {"color": "gray"},
                    }
                ]
            },
        })

        # Link (bookmark)
        if item.url:
            children.append({
                "object": "block",
                "type": "bookmark",
                "bookmark": {
                    "url": item.url,
                },
            })

        # Bloco toggle principal
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": item.title},
                        "annotations": {"bold": True},
                    }
                ],
                "children": children,
            },
        }

    def _heading_block(self, text: str, level: int = 2) -> dict:
        """Cria um bloco de heading."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text},
                    }
                ]
            },
        }

    def _divider_block(self) -> dict:
        """Cria um bloco divisor."""
        return {
            "object": "block",
            "type": "divider",
            "divider": {},
        }

    def test_connection(self) -> bool:
        """Testa se a conexão com o Notion está funcionando."""
        url = f"{NOTION_BASE_URL}/pages/{self.page_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                page_data = response.json()
                title = "Página encontrada"
                # Tenta extrair o título
                props = page_data.get("properties", {})
                for prop in props.values():
                    if prop.get("type") == "title":
                        titles = prop.get("title", [])
                        if titles:
                            title = titles[0].get("plain_text", title)
                        break
                logger.info(f"Conexão Notion OK: {title}")
                return True
            else:
                logger.error(
                    f"Erro ao conectar Notion: {response.status_code} - "
                    f"{response.text[:200]}"
                )
                return False
        except requests.RequestException as e:
            logger.error(f"Erro de rede ao testar Notion: {e}")
            return False
