"""
Módulo de curadoria e filtragem de conteúdo.
Filtra, pontua e seleciona os artigos mais relevantes para o público-alvo:
profissionais de economia real sem background técnico em IA.
"""

import logging
import re
from collections import Counter

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from executions.scrapers.base_scraper import ScrapedItem

logger = logging.getLogger(__name__)

# Palavras-chave que aumentam relevância para o público-alvo
POSITIVE_KEYWORDS = [
    # Negócios
    "business", "empresa", "negócio", "negocio", "company", "startup",
    "empreendedor", "entrepreneur", "revenue", "receita", "profit",
    "marketing", "sales", "vendas", "roi", "produtividade", "productivity",
    "eficiência", "efficiency", "automação", "automation", "workflow",
    # Setores econômicos
    "indústria", "industry", "manufatura", "manufacturing", "agro",
    "agronegócio", "agribusiness", "comércio", "commerce", "retail",
    "varejo", "serviços", "services", "logística", "logistics",
    "supply chain", "cadeia de suprimentos",
    # IA aplicada
    "ai tool", "ferramenta de ia", "chatgpt", "copilot", "assistente",
    "assistant", "no-code", "low-code", "ai agent", "agente de ia",
    "prompt", "generative ai", "ia generativa",
    # Impacto prático
    "how to", "como usar", "tutorial", "guia", "guide", "dica", "tip",
    "case study", "caso de uso", "use case", "example", "exemplo",
    "free", "grátis", "gratuito", "launch", "lançamento", "new tool",
    "nova ferramenta", "trending", "future", "futuro",
    # RH e gestão
    "hr", "recursos humanos", "human resources", "manager", "gestor",
    "gestão", "management", "team", "equipe", "hiring", "contratação",
    "career", "carreira",
]

# Palavras-chave que reduzem relevância (conteúdo muito técnico)
NEGATIVE_KEYWORDS = [
    "arxiv", "paper", "benchmark", "fine-tune", "fine-tuning",
    "transformer", "attention mechanism", "gradient", "backpropagation",
    "pytorch", "tensorflow", "cuda", "gpu cluster", "training loss",
    "epoch", "hyperparameter", "rlhf", "token limit", "context window",
    "embedding", "vector database", "rag pipeline", "langchain",
    "llama weights", "model weights", "checkpoint", "quantization",
    "inference speed", "vram", "kernel", "compiler", "assembly",
    "leetcode", "algorithm", "data structure",
]

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

POSITIVE_KEYWORDS_LOWER = [kw.lower() for kw in POSITIVE_KEYWORDS]
NEGATIVE_KEYWORDS_LOWER = [kw.lower() for kw in NEGATIVE_KEYWORDS]


class ContentCurator:
    """Filtra e pontua conteúdo para o público-alvo."""

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

        # 3. Separa por fonte (cada uma tem inclusão garantida)
        newsletters = [i for i in items if i.source == "Newsletter"]
        reddit = [i for i in items if i.source == "Reddit"]
        youtube = [i for i in items if i.source == "YouTube"]
        others = [i for i in items if i.source not in ("Newsletter", "Reddit", "YouTube")]

        logger.info(
            f"  Newsletters: {len(newsletters)} | Reddit: {len(reddit)} | "
            f"YouTube: {len(youtube)} | Outros: {len(others)}"
        )

        # 4. Pontua relevância de cada grupo
        newsletters = self._score_relevance(newsletters)
        reddit = self._score_relevance(reddit)
        youtube = self._score_relevance(youtube)
        others = self._score_relevance(others)

        # 5. Ordena cada grupo por relevância
        newsletters.sort(key=lambda x: x.relevance_score, reverse=True)
        reddit.sort(key=lambda x: x.relevance_score, reverse=True)
        youtube.sort(key=lambda x: x.relevance_score, reverse=True)
        others.sort(key=lambda x: x.relevance_score, reverse=True)

        # 6. Garante slots para cada fonte, depois preenche com sobra
        selected = youtube + reddit + newsletters + others
        selected = selected[:max_items]

        nl_count = len([i for i in selected if i.source == "Newsletter"])
        rd_count = len([i for i in selected if i.source == "Reddit"])
        yt_count = len([i for i in selected if i.source == "YouTube"])
        logger.info(
            f"  Selecionados: {len(selected)} itens finais "
            f"({nl_count} newsletters + {rd_count} reddit + {yt_count} youtube)"
        )

        return selected

    def _deduplicate(self, items: list[ScrapedItem]) -> list[ScrapedItem]:
        """Remove itens duplicados por URL ou título similar."""
        seen_urls = set()
        seen_titles = set()
        unique = []

        for item in items:
            # Normaliza URL
            url_key = item.url.rstrip("/").lower()
            if url_key in seen_urls:
                continue

            # Normaliza título para comparação
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

            is_spam = False
            for pattern in SPAM_PATTERNS:
                if pattern.search(full_text):
                    is_spam = True
                    logger.debug(f"  Spam detectado: {item.title[:60]}")
                    break

            if not is_spam:
                filtered.append(item)

        return filtered

    def _score_relevance(self, items: list[ScrapedItem]) -> list[ScrapedItem]:
        """Pontua cada item com base em keywords e heurísticas."""
        for item in items:
            score = item.relevance_score  # Mantém score original (upvotes, etc.)
            full_text = f"{item.title} {item.description}".lower()

            # Bonus por palavras positivas
            for keyword in POSITIVE_KEYWORDS_LOWER:
                if keyword in full_text:
                    score += 10

            # Penalidade por conteúdo muito técnico
            tech_count = 0
            for keyword in NEGATIVE_KEYWORDS_LOWER:
                if keyword in full_text:
                    tech_count += 1
                    score -= 5

            # Se o conteúdo é excessivamente técnico, penaliza mais
            if tech_count > 3:
                score -= 20

            # Bonus por ter descrição substancial
            if len(item.description) > 100:
                score += 5

            # Bonus por título claro (não muito curto nem muito longo)
            if 20 < len(item.title) < 100:
                score += 3

            item.relevance_score = max(0, score)

        return items

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação de similaridade."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        # Pega as primeiras 8 palavras para comparação
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
