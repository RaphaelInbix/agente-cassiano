#!/bin/bash
set -e

# Exporta variáveis de ambiente para o cron
printenv | grep -E '^(NOTION_|ANTHROPIC_|REDDIT_|PORT=)' >> /etc/environment

# Inicia o cron em background
cron

# Inicia o Gunicorn
exec gunicorn wsgi:app \
    --bind 0.0.0.0:${PORT:-8080} \
    --timeout 180 \
    --workers 1 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
