"""
WSGI entry point para produção (Render/Gunicorn).
"""
import sys
import os

print("=== WSGI: Starting import ===", flush=True)

# Garante que a raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from api.server import app
    print("=== WSGI: Import OK ===", flush=True)
except Exception as e:
    print(f"=== WSGI: IMPORT FAILED: {e} ===", flush=True)
    import traceback
    traceback.print_exc()
    raise

if __name__ == "__main__":
    app.run()
