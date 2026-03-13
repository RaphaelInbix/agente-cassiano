"""
Script executado pelo cron para rodar o pipeline de curadoria.
Roda 3x/semana (seg, qua, sex às 07:00 BRT).
"""

import sys
import os
import logging
from datetime import datetime

# Garante que a raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cron_runner")


def main():
    logger.info(f"=== Cron: Iniciando pipeline - {datetime.now().isoformat()} ===")

    try:
        from api.server import run_pipeline, save_data, load_data, save_data_raw
        from executions.integrations.notion_client import NotionClient

        # Executa o pipeline
        items = run_pipeline()

        if not items:
            logger.warning("Cron: Nenhum item coletado")
            return

        # Salva dados localmente
        save_data(items)
        logger.info(f"Cron: {len(items)} itens salvos localmente")

        # Publica no Notion
        try:
            notion = NotionClient()
            cache_data = load_data()

            # Verifica se deve fazer clear+publish completo (a cada 3 dias)
            should_full_publish = True
            last_clear = cache_data.get("last_notion_clear")
            if last_clear:
                try:
                    last_dt = datetime.fromisoformat(last_clear)
                    if (datetime.now() - last_dt).total_seconds() < 3 * 86400:
                        should_full_publish = False
                except (ValueError, TypeError):
                    pass

            if should_full_publish:
                notion.clear_page()
                notion.publish(items)
                cache_data["last_notion_clear"] = datetime.now().isoformat()
                logger.info("Cron: Publicação completa no Notion")
            else:
                notion.delete_cache_blocks()
                logger.info("Cron: Apenas atualizando cache no Notion")

            notion.save_cache(cache_data)
            save_data_raw(cache_data)

        except Exception as e:
            logger.error(f"Cron: Erro ao publicar no Notion: {e}")

    except Exception as e:
        logger.error(f"Cron: Erro no pipeline: {e}", exc_info=True)

    logger.info(f"=== Cron: Finalizado - {datetime.now().isoformat()} ===")


if __name__ == "__main__":
    main()
