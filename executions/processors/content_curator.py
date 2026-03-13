"""
Módulo de curadoria e filtragem de conteúdo.
Usa Claude 3.5 Sonnet para avaliar relevância semanticamente,
com fallback para scoring por keywords se a API falhar.

Público-alvo: profissionais de economia real sem background técnico em IA.
"""

import json
import logging
import re
from collections import Counter

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from executions.scrapers.base_scraper import ScrapedItem
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL, CURATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Conteúdo que deve ser filtrado (spam, irrelevante)
SPAM_PATTERNS = [
    re.compile(r"(?i)onlyfans"),
    re.compile(r"(?i)crypto.*pump"),
    re.compile(r"(?i)free money"),
    re.compile(r"(?i)click here to win"),
    re.compile(r"(?i)subscribe.*free"),
    re.compile(r"(?i)\$\d+.*per day"),
    re.compile(r"(?i)get rich"),
]

# Fallback keywords (usadas quando a API Claude não está disponível)
POSITIVE_KEYWORDS_LOWER = [
    "business", "empresa", "negócio", "startup", "marketing", "sales",
    "vendas", "produtividade", "automação", "automation", "workflow",
    "ai tool", "ferramenta de ia", "chatgpt", "copilot", "assistente",
    "no-code", "low-code", "ai agent", "prompt", "ia generativa",
    "how to", "como usar", "tutorial", "guia", "case study", "trending",
    "hr", "recursos humanos", "manager", "gestão", "career", "carreira",
]

NEGATIVE_KEYWORDS_LOWER = [
    "arxiv", "paper", "benchmark", "fine-tune", "fine-tuning",
    "transformer", "attention mechanism", "gradient", "backpropagation",
    "pytorch", "tensorflow", "cuda", "gpu cluster", "training loss",
    "epoch", "hyperparameter", "rlhf", "embedding", "vector database",
    "langchain", "model weights", "checkpoint", "quantization",
    "vram", "kernel", "compiler", "leetcode", "algorithm",
]


class ContentCurator:
    """Filtra e pontua conteúdo para o público-alvo usando Claude API."""

    def __init__(self):
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

    def curate(
        self, items: list[ScrapedItem], max_items: int = 30
    ) -> list[ScrapedItem]:
        """Pipeline completo de curadoria."""
        logger.info(f"Iniciando curadoria de {len(items)} itens...")

        # 1. Remove duplicatas
        items = self._deduplicate(items)
        logger.info(f"  Após deduplicação: {len(items)} itens")

        # 2. Remove spam
        items = self._filter_spam(items)
        logger.info(f"  Após filtro de spam: {len(items)} itens")

        # 3. Pontua relevância via Claude (ou fallback por keywords)
        items = self._score_with_claude(items)

        # 4. Ordena por relevância
        items.sort(key=lambda x: x.relevance_score, reverse=True)

        # 5. Seleciona os melhores
        selected = items[:max_items]

        # Log por fonte
        sources = Counter(i.source for i in selected)
        logger.info(
            f"  Selecionados: {len(selected)} itens finais "
            f"({sources})"
        )

        return selected

    def _score_with_claude(self, items: list[ScrapedItem]) -> list[ScrapedItem]:
        """Pontua itens usando Claude API. Fallback para keywords se falhar."""
        client = self._get_client()
        if not client:
            logger.warning("Claude API indisponível — usando fallback por keywords")
            return self._score_relevance_fallback(items)

        # Processa em batches de 15 para economizar tokens
        batch_size = 15
        scored_items = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                scores = self._call_claude_for_scores(client, batch)
                for idx, item in enumerate(batch):
                    if idx in scores:
                        item.relevance_score = scores[idx]
                    # Mantém score original se Claude não retornou para este item
                scored_items.extend(batch)
            except Exception as e:
                logger.error(f"Erro na curadoria Claude (batch {i}): {e}")
                # Fallback para este batch
                scored_items.extend(self._score_relevance_fallback(batch))

        return scored_items

    def _call_claude_for_scores(
        self, client, batch: list[ScrapedItem]
    ) -> dict[int, float]:
        """Chama Claude API para pontuar um batch de itens."""
        # Monta a lista de itens para o prompt
        items_text = []
        for idx, item in enumerate(batch):
            desc = item.description[:200] if item.description else "(sem descrição)"
            items_text.append(
                f"[{idx}] Fonte: {item.source}/{item.channel}\n"
                f"    Título: {item.title}\n"
                f"    Descrição: {desc}"
            )

        user_message = (
            "Avalie os itens abaixo e retorne APENAS o JSON array com scores.\n\n"
            + "\n\n".join(items_text)
        )

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=CURATION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        # Parse da resposta
        response_text = response.content[0].text.strip()
        # Remove possível markdown wrapping
        if response_text.startswith("```"):
            response_text = re.sub(r"^```\w*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        scores_list = json.loads(response_text)
        return {item["index"]: item["score"] for item in scores_list}

    def _score_relevance_fallback(
        self, items: list[ScrapedItem]
    ) -> list[ScrapedItem]:
        """Fallback: pontua cada item com base em keywords (sem API)."""
        for item in items:
            score = item.relevance_score
            full_text = f"{item.title} {item.description}".lower()

            for keyword in POSITIVE_KEYWORDS_LOWER:
                if keyword in full_text:
                    score += 10

            tech_count = 0
            for keyword in NEGATIVE_KEYWORDS_LOWER:
                if keyword in full_text:
                    tech_count += 1
                    score -= 5

            if tech_count > 3:
                score -= 20

            if len(item.description) > 100:
                score += 5
            if 20 < len(item.title) < 100:
                score += 3

            item.relevance_score = max(0, score)

        return items

    def _deduplicate(self, items: list[ScrapedItem]) -> list[ScrapedItem]:
        """Remove itens duplicados por URL ou título similar."""
        seen_urls = set()
        seen_titles = set()
        unique = []

        for item in items:
            url_key = item.url.rstrip("/").lower()
            if url_key in seen_urls:
                continue

            title_key = self._normalize_text(item.title)
            if title_key in seen_titles:
                continue

            seen_urls.add(url_key)
            seen_titles.add(title_key)
            unique.append(item)

        return unique

    def _filter_spam(self, items: list[ScrapedItem]) -> list[ScrapedItem]:
        """Remove conteúdo spam ou irrelevante."""
        filtered = []
        for item in items:
            full_text = f"{item.title} {item.description}".lower()
            is_spam = any(pattern.search(full_text) for pattern in SPAM_PATTERNS)
            if not is_spam:
                filtered.append(item)
            else:
                logger.debug(f"  Spam detectado: {item.title[:60]}")
        return filtered

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação de similaridade."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        words = text.split()[:8]
        return " ".join(words)

    def get_summary_stats(self, items: list[ScrapedItem]) -> dict:
        """Retorna estatísticas da curadoria para logging."""
        sources = Counter(item.source for item in items)
        channels = Counter(item.channel for item in items)
        avg_score = (
            sum(item.relevance_score for item in items) / len(items)
            if items
            else 0
        )
        return {
            "total_items": len(items),
            "by_source": dict(sources),
            "by_channel": dict(channels),
            "avg_relevance_score": round(avg_score, 2),
            "top_item": items[0].title if items else "N/A",
        }
