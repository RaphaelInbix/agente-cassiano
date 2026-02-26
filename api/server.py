"""
API REST para a Curadoria Inbix.
Expõe endpoints para consumo do frontend React.
"""

import json
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime

# Garante que a raiz do projeto está no path (local e produção)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import Flask, jsonify, request
from flask_cors import CORS

from executions.scrapers.newsletter_scraper import NewsletterScraper
from executions.scrapers.reddit_scraper import RedditScraper
from executions.scrapers.youtube_scraper import YouTubeScraper
from executions.processors.content_curator import ContentCurator
from executions.integrations.notion_client import NotionClient

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "curadoria.json")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")


def save_status(status: str, detail: str = ""):
    """Salva o status atual do pipeline."""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "status": status,
        "detail": detail,
        "timestamp": datetime.now().isoformat(),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_status():
    """Carrega o status atual."""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "idle", "detail": "", "timestamp": None}


def run_pipeline():
    """Executa o pipeline de coleta e curadoria (newsletters + reddit em paralelo)."""
    all_items = []
    save_status("running", "Coletando newsletters, Reddit e YouTube em paralelo...")

    def _scrape_newsletters():
        try:
            scraper = NewsletterScraper()
            items = scraper.scrape()
            logger.info(f"Newsletters: {len(items)} artigos coletados")
            return items
        except Exception as e:
            logger.error(f"Erro ao coletar newsletters: {e}")
            return []

    def _scrape_reddit():
        try:
            scraper = RedditScraper()
            items = scraper.scrape()
            items.sort(key=lambda x: x.relevance_score, reverse=True)
            logger.info(f"Reddit: {len(items)} posts coletados")
            return items[:15]
        except Exception as e:
            logger.error(f"Erro ao coletar Reddit: {e}")
            return []

    def _scrape_youtube():
        try:
            scraper = YouTubeScraper()
            items = scraper.scrape()
            logger.info(f"YouTube: {len(items)} vídeos coletados")
            return items
        except Exception as e:
            logger.error(f"Erro ao coletar YouTube: {e}")
            return []

    with ThreadPoolExecutor(max_workers=3) as pool:
        nl_future = pool.submit(_scrape_newsletters)
        rd_future = pool.submit(_scrape_reddit)
        yt_future = pool.submit(_scrape_youtube)
        all_items.extend(nl_future.result())
        all_items.extend(rd_future.result())
        all_items.extend(yt_future.result())

    if not all_items:
        save_status("done", "Nenhum item coletado")
        return []

    save_status("running", "Aplicando curadoria...")
    curator = ContentCurator()
    curated = curator.curate(all_items, max_items=45)
    return curated


def run_pipeline_background():
    """Executa o pipeline em background thread."""
    try:
        save_status("running", "Iniciando coleta...")
        items = run_pipeline()
        save_data(items)

        # Marca como done para o frontend ANTES de publicar no Notion
        save_status("done", f"{len(items)} itens atualizados")

        # Publica no Notion em seguida (não bloqueia o frontend)
        if items:
            try:
                notion = NotionClient()
                notion.publish(items)
                logger.info("Publicação no Notion concluída")
            except Exception as e:
                logger.error(f"Erro ao publicar no Notion: {e}")

    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        save_status("error", str(e))


def save_data(items):
    """Salva itens curados em JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "updated_at": datetime.now().isoformat(),
        "total": len(items),
        "items": [asdict(item) for item in items],
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def load_data():
    """Carrega dados do cache JSON."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"updated_at": None, "total": 0, "items": []}


@app.route("/api/curadoria", methods=["GET"])
def get_curadoria():
    """Retorna os dados curados do cache."""
    data = load_data()
    return jsonify(data)


@app.route("/api/atualizar", methods=["POST"])
def atualizar():
    """Inicia o pipeline em background e retorna imediatamente."""
    status = load_status()
    if status.get("status") == "running":
        return jsonify({"success": True, "message": "Atualização já em andamento"})

    thread = threading.Thread(target=run_pipeline_background, daemon=True)
    thread.start()
    return jsonify({"success": True, "message": "Atualização iniciada"})


@app.route("/api/status", methods=["GET"])
def get_status():
    """Retorna o status atual do pipeline."""
    return jsonify(load_status())


@app.route("/api/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.run(host="0.0.0.0", port=5000, debug=True)
