"""
Configurações centrais do Agente Cassiano.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da raiz do projeto
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ============================================================
# NOTION
# ============================================================
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")
NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# ============================================================
# FONTES - NEWSLETTERS
# ============================================================
NEWSLETTERS = [
    {
        "name": "The Neuron Daily",
        "url": "https://www.theneurondaily.com/",
        "max_articles": 5,
    },
    {
        "name": "TechDrop News",
        "url": "https://www.techdrop.news/",
        "max_articles": 5,
    },
    {
        "name": "The Rundown AI",
        "url": "https://www.therundown.ai/",
        "max_articles": 5,
    },
]

# ============================================================
# FONTES - REDDIT
# ============================================================
REDDIT_SUBREDDITS = [
    {
        "name": "r/AIToolMadeEasy",
        "url": "https://www.reddit.com/r/AIToolMadeEasy/",
        "search_terms": None,
        "max_posts": 10,
    },
    {
        "name": "r/ChatGPT",
        "url": "https://www.reddit.com/r/ChatGPT/",
        "search_terms": ["Marketing", "Manager", "HR", "Sales", "future", "trending"],
        "max_posts": 10,
    },
{
        "name": "r/NextGenAITool",
        "url": "https://www.reddit.com/r/NextGenAITool/",
        "search_terms": None,
        "max_posts": 10,
    },
    {
        "name": "r/singularity",
        "url": "https://www.reddit.com/r/singularity/",
        "search_terms": None,
        "max_posts": 10,
    },
    {
        "name": "r/ChatGPTpro",
        "url": "https://www.reddit.com/r/ChatGPTpro/",
        "search_terms": ["how to"],
        "max_posts": 10,
    },
    {
        "name": "r/AIforSmallBusiness",
        "url": "https://www.reddit.com/r/AIforSmallBusiness/",
        "search_terms": None,
        "max_posts": 10,
    },
    {
        "name": "r/ClaudeAI",
        "url": "https://www.reddit.com/r/ClaudeAI/",
        "search_terms": None,
        "max_posts": 10,
    },
    {
        "name": "r/ArtificialInteligence",
        "url": "https://www.reddit.com/r/ArtificialInteligence/",
        "search_terms": None,
        "max_posts": 10,
    },
    {
        "name": "r/AI_Agents",
        "url": "https://www.reddit.com/r/AI_Agents/",
        "search_terms": None,
        "max_posts": 10,
    },
]



# ============================================================
# SCRAPING
# ============================================================
REQUEST_TIMEOUT = 30  # segundos
REQUEST_DELAY = 2  # segundos entre requisições (anti-ban)
MAX_RETRIES = 3

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# ============================================================
# LOGGING
# ============================================================
LOG_DIR = "logs"
LOG_LEVEL = "INFO"
