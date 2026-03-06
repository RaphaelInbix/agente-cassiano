"""
Cliente para a API do Notion.
Salva os artigos curados como blocos toggle na página configurada.
Também armazena/restaura cache JSON para persistência entre deploys.
"""

import json
import logging
import requests
from datetime import datetime, timezone, timedelta

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

    def clear_page(self) -> bool:
        """Remove todos os blocos filhos da página do Notion (limpa publicações antigas)."""
        logger.info("Limpando blocos antigos da página do Notion...")
        blocks = self._get_child_blocks()
        if blocks is None:
            logger.error("Não foi possível obter blocos da página.")
            return False

        if not blocks:
            logger.info("Página já está vazia.")
            return True

        deleted = 0
        for block in blocks:
            block_id = block.get("id")
            if not block_id:
                continue
            url = f"{NOTION_BASE_URL}/blocks/{block_id}"
            try:
                resp = requests.delete(url, headers=self.headers)
                if resp.status_code == 200:
                    deleted += 1
                else:
                    logger.warning(f"Erro ao deletar bloco {block_id}: {resp.status_code}")
            except requests.RequestException as e:
                logger.error(f"Erro de rede ao deletar bloco: {e}")

        logger.info(f"Limpeza concluída: {deleted}/{len(blocks)} blocos removidos.")
        return deleted == len(blocks)

    def _get_child_blocks(self) -> list[dict] | None:
        """Lista todos os blocos filhos da página (com paginação)."""
        url = f"{NOTION_BASE_URL}/blocks/{self.page_id}/children"
        all_blocks = []
        start_cursor = None

        while True:
            params = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor

            try:
                resp = requests.get(url, headers=self.headers, params=params)
                if resp.status_code != 200:
                    logger.error(f"Erro ao listar blocos: {resp.status_code} - {resp.text[:300]}")
                    return None

                data = resp.json()
                all_blocks.extend(data.get("results", []))

                if not data.get("has_more"):
                    break
                start_cursor = data.get("next_cursor")
            except requests.RequestException as e:
                logger.error(f"Erro de rede ao listar blocos: {e}")
                return None

        return all_blocks

    def publish(self, items: list[ScrapedItem]) -> bool:
        """Publica todos os itens curados na página do Notion."""
        logger.info(f"Publicando {len(items)} itens no Notion...")

        # Agrupa por fonte
        newsletters = [i for i in items if i.source == "Newsletter"]
        reddit_posts = [i for i in items if i.source == "Reddit"]
        youtube_videos = [i for i in items if i.source == "YouTube"]
        x_posts = [i for i in items if i.source == "X (Twitter)"]

        blocks = []

        # Header com data
        blocks.append(self._heading_block(
            f"Curadoria Semanal - {datetime.now().strftime('%d/%m/%Y')}",
            level=1,
        ))
        blocks.append(self._divider_block())

        # Seção YouTube (prioridade)
        if youtube_videos:
            blocks.append(self._heading_block("YouTube", level=2))
            for item in youtube_videos:
                blocks.append(self._toggle_block(item))

        # Seção Reddit
        if reddit_posts:
            blocks.append(self._heading_block("Reddit", level=2))
            for item in reddit_posts:
                blocks.append(self._toggle_block(item))

        # Seção Newsletters
        if newsletters:
            blocks.append(self._heading_block("Newsletters", level=2))
            for item in newsletters:
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

    def save_cache(self, data: dict) -> bool:
        """Salva dados da curadoria como code block no Notion (persistência entre deploys)."""
        logger.info("Salvando cache JSON no Notion...")
        json_str = json.dumps(data, ensure_ascii=False)

        # Notion limita 2000 chars por rich_text element; chunk it
        CHUNK = 2000
        chunks = [json_str[i:i + CHUNK] for i in range(0, len(json_str), CHUNK)]

        # Marker heading so we can find it later
        blocks = [
            {
                "object": "block",
                "type": "divider",
                "divider": {},
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "CACHE_JSON_DATA"}}],
                },
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [
                        {"type": "text", "text": {"content": chunk}}
                        for chunk in chunks
                    ],
                    "language": "json",
                },
            },
        ]
        return self._append_blocks(blocks)

    def delete_cache_blocks(self) -> bool:
        """Remove apenas os blocos de cache (divider + heading CACHE_JSON_DATA + code)."""
        blocks = self._get_child_blocks()
        if blocks is None:
            return False

        found_marker = False
        to_delete = []
        for i, block in enumerate(blocks):
            if not found_marker:
                # O divider vem logo antes do heading
                if block.get("type") == "heading_3":
                    texts = block.get("heading_3", {}).get("rich_text", [])
                    if any("CACHE_JSON_DATA" in t.get("text", {}).get("content", "") for t in texts):
                        found_marker = True
                        to_delete.append(block.get("id"))
                        # Divider anterior
                        if i > 0 and blocks[i - 1].get("type") == "divider":
                            to_delete.append(blocks[i - 1].get("id"))
                continue
            # Após o marker, pega o code block e para
            if block.get("type") == "code":
                to_delete.append(block.get("id"))
                break

        for block_id in to_delete:
            if block_id:
                try:
                    requests.delete(
                        f"{NOTION_BASE_URL}/blocks/{block_id}",
                        headers=self.headers,
                    )
                except requests.RequestException:
                    pass

        return True

    def read_cache(self) -> dict | None:
        """Lê o cache JSON salvo no Notion. Retorna None se não encontrado."""
        logger.info("Tentando restaurar cache do Notion...")
        blocks = self._get_child_blocks()
        if blocks is None:
            return None

        # Find the code block after the CACHE_JSON_DATA heading
        found_marker = False
        for block in blocks:
            if not found_marker:
                if block.get("type") == "heading_3":
                    texts = block.get("heading_3", {}).get("rich_text", [])
                    if any("CACHE_JSON_DATA" in t.get("text", {}).get("content", "") for t in texts):
                        found_marker = True
                continue

            if block.get("type") == "code":
                rich_text = block.get("code", {}).get("rich_text", [])
                json_str = "".join(t.get("text", {}).get("content", "") for t in rich_text)
                try:
                    data = json.loads(json_str)
                    logger.info(f"Cache restaurado do Notion: {data.get('total', 0)} itens")
                    return data
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Erro ao parsear cache do Notion: {e}")
                    return None

        logger.info("Nenhum cache encontrado no Notion.")
        return None

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
