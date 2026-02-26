"""
Agente Cassiano - Ponto de entrada principal.
Monitoramento semanal de IA, Tecnologia e Negócios do Futuro.

Uso:
    python main.py          # Executa o pipeline completo
    python main.py --test   # Apenas testa conexões
"""

import sys
import os

# Garante que o diretório raiz está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.orchestrator import run, setup_logging, logger
from executions.integrations.notion_client import NotionClient


def test_connections():
    """Testa as conexões antes de rodar o pipeline."""
    setup_logging()
    logger.info("Modo de teste - verificando conexões...")

    # Teste Notion
    notion = NotionClient()
    notion_ok = notion.test_connection()
    print(f"\nNotion: {'OK' if notion_ok else 'FALHA'}")

    # Teste Reddit (JSON público com fallback de domínios)
    from executions.scrapers.reddit_scraper import RedditScraper
    reddit = RedditScraper()
    data = reddit._reddit_json(
        "r/AIToolMadeEasy/top.json",
        params={"t": "week", "limit": 1, "raw_json": 1},
    )
    reddit_ok = data is not None and "data" in data
    print(f"Reddit:  {'OK' if reddit_ok else 'FALHA'}")

    # Teste Newsletter
    from executions.scrapers.newsletter_scraper import NewsletterScraper
    nl = NewsletterScraper()
    html = nl.fetch_page("https://www.theneurondaily.com/")
    nl_ok = html is not None and len(html) > 100
    print(f"Neuron:  {'OK' if nl_ok else 'FALHA'}")

    print(f"\nResultado geral: {'TUDO OK' if all([notion_ok, reddit_ok, nl_ok]) else 'VERIFICAR FALHAS'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_connections()
    else:
        run()
