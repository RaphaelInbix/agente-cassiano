"""
WSGI entry point para produção (Render/Gunicorn).
"""
import sys
import os

# Garante que a raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.server import app

if __name__ == "__main__":
    app.run()
