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
# OAuth credentials (registrar app em https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_SUBREDDITS = [
    {
        "name": "r/AIToolMadeEasy",
        "url": "https://www.reddit.com/r/AIToolMadeEasy/",
        "search_terms": None,
        "max_posts": 5,
    },
    {
        "name": "r/ChatGPT",
        "url": "https://www.reddit.com/r/ChatGPT/",
        "search_terms": ["Marketing", "Manager", "HR", "Sales", "future", "trending"],
        "max_posts": 5,
    },
    {
        "name": "r/NextGenAITool",
        "url": "https://www.reddit.com/r/NextGenAITool/",
        "search_terms": None,
        "max_posts": 5,
    },
    {
        "name": "r/singularity",
        "url": "https://www.reddit.com/r/singularity/",
        "search_terms": None,
        "max_posts": 5,
    },
    {
        "name": "r/ChatGPTpro",
        "url": "https://www.reddit.com/r/ChatGPTpro/",
        "search_terms": ["how to"],
        "max_posts": 5,
    },
    {
        "name": "r/AIforSmallBusiness",
        "url": "https://www.reddit.com/r/AIforSmallBusiness/",
        "search_terms": None,
        "max_posts": 5,
    },
    {
        "name": "r/ClaudeAI",
        "url": "https://www.reddit.com/r/ClaudeAI/",
        "search_terms": None,
        "max_posts": 5,
    },
    {
        "name": "r/ArtificialInteligence",
        "url": "https://www.reddit.com/r/ArtificialInteligence/",
        "search_terms": None,
        "max_posts": 5,
    },
    {
        "name": "r/AI_Agents",
        "url": "https://www.reddit.com/r/AI_Agents/",
        "search_terms": None,
        "max_posts": 5,
    },
]


# ============================================================
# FONTES - YOUTUBE (RSS Feeds)
# ============================================================
YOUTUBE_CHANNELS = [
    {"name": "Deborah Folloni", "handle": "deborahfolloni"},
    {"name": "Jovens de Negócios", "handle": "jovensdenegocios"},
    {"name": "No Code Startup", "handle": "nocodestartup"},
    {"name": "Código Fonte TV", "handle": "codigofontetv"},
    {"name": "Matheus Battisti", "handle": "MatheusBattisti"},
    {"name": "Hora de Negócios", "handle": "horadenegocios"},
    {"name": "Andre Prado", "handle": "AndrePrado"},
    {"name": "MrEflow", "handle": "mreflow"},
    {"name": "AI Explained", "handle": "aiexplained-official"},
]

YOUTUBE_KEYWORDS = [
    "DeepSeek", "NVIDIA", "Sora", "Anthropic", "Opus", "Claude code", "Claude",
    "Cursor", "antigravity", "gemini", "IA", "AI", "TOOLS", "NANO BANANA",
    "Chatgpt", "GPT", "LLM", "OpenClaw", "OpenAI", "n8n", "N8N", "Supabase",
]

YOUTUBE_MAX_RESULTS = 15  # top vídeos após filtro por keywords

# ============================================================
# SCRAPING
# ============================================================
REQUEST_TIMEOUT = 10  # segundos
REQUEST_DELAY = 0.3  # segundos entre requisições (anti-ban)
MAX_RETRIES = 2

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
