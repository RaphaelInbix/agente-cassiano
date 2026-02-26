"""
Orquestrador principal do Agente Cassiano.
Coordena o fluxo: Scraping -> Curadoria -> Publicação no Notion.
"""

import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from executions.scrapers.newsletter_scraper import NewsletterScraper
from executions.scrapers.reddit_scraper import RedditScraper
from executions.processors.content_curator import ContentCurator
from executions.integrations.notion_client import NotionClient
from config.settings import LOG_DIR, LOG_LEVEL

logger = logging.getLogger("agente_cassiano")


def setup_logging():
    """Configura o sistema de logging."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"run_{timestamp}.log")

    # StreamHandler com encoding UTF-8 para suportar emojis no console Windows
    stream_handler = logging.StreamHandler(
        open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
    )

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            stream_handler,
        ],
    )
    return log_file


def run():
    """Executa o pipeline completo do agente."""
    log_file = setup_logging()
    logger.info("=" * 60)
    logger.info("AGENTE CASSIANO - Início da execução")
    logger.info(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # ETAPA 0: Testar conexão com Notion
    # ------------------------------------------------------------------
    logger.info("\n[ETAPA 0] Testando conexão com Notion...")
    notion = NotionClient()
    if not notion.test_connection():
        logger.error("Falha na conexão com Notion. Verifique token e page ID.")
        logger.error("Continuando coleta para debug, mas publicação pode falhar.")

    # ------------------------------------------------------------------
    # ETAPA 1: COLETA (Scraping)
    # ------------------------------------------------------------------
    logger.info("\n[ETAPA 1] Iniciando coleta de dados...")
    all_items = []

    # Newsletters
    logger.info("\n--- Newsletters ---")
    try:
        newsletter_scraper = NewsletterScraper()
        newsletter_items = newsletter_scraper.scrape()
        all_items.extend(newsletter_items)
        logger.info(f"Total newsletters: {len(newsletter_items)} artigos")
    except Exception as e:
        logger.error(f"Erro no scraping de newsletters: {e}")

    # Reddit (seleciona apenas os 5 mais relevantes de todos os subreddits)
    logger.info("\n--- Reddit ---")
    try:
        reddit_scraper = RedditScraper()
        reddit_items = reddit_scraper.scrape()
        logger.info(f"Reddit coletados: {len(reddit_items)} posts brutos")

        # Ordena por relevância e seleciona apenas os top 15
        reddit_items.sort(key=lambda x: x.relevance_score, reverse=True)
        reddit_items = reddit_items[:15]
        all_items.extend(reddit_items)
        logger.info(f"Reddit selecionados: {len(reddit_items)} posts (top 15)")
    except Exception as e:
        logger.error(f"Erro no scraping do Reddit: {e}")

    logger.info(f"\nTotal coletado: {len(all_items)} itens de todas as fontes")

    if not all_items:
        logger.warning("Nenhum item coletado. Encerrando.")
        return

    # ------------------------------------------------------------------
    # ETAPA 2: CURADORIA (Filtragem e Pontuação)
    # ------------------------------------------------------------------
    logger.info("\n[ETAPA 2] Iniciando curadoria de conteúdo...")
    curator = ContentCurator()
    curated_items = curator.curate(all_items, max_items=30)

    # Log das estatísticas
    stats = curator.get_summary_stats(curated_items)
    logger.info(f"Estatísticas da curadoria:")
    logger.info(f"  Total selecionados: {stats['total_items']}")
    logger.info(f"  Por fonte: {stats['by_source']}")
    logger.info(f"  Por canal: {stats['by_channel']}")
    logger.info(f"  Score médio: {stats['avg_relevance_score']}")
    logger.info(f"  Top artigo: {stats['top_item']}")

    if not curated_items:
        logger.warning("Nenhum item passou pela curadoria. Encerrando.")
        return

    # ------------------------------------------------------------------
    # ETAPA 3: PUBLICAÇÃO (Notion)
    # ------------------------------------------------------------------
    logger.info("\n[ETAPA 3] Publicando no Notion...")
    success = notion.publish(curated_items)

    # ------------------------------------------------------------------
    # RESUMO FINAL
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("AGENTE CASSIANO - Execução finalizada")
    logger.info(f"Status: {'SUCESSO' if success else 'COM ERROS'}")
    logger.info(f"Itens publicados: {len(curated_items)}")
    logger.info(f"Log salvo em: {log_file}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
