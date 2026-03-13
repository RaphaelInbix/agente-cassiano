# ============================================================
# Stage 1: Build frontend React
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /app/curadoria-web
COPY curadoria-web/package.json curadoria-web/package-lock.json* ./
RUN npm install
COPY curadoria-web/ ./
RUN npm run build

# ============================================================
# Stage 2: Python backend + frontend estático
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código backend
COPY api/ api/
COPY config/ config/
COPY executions/ executions/
COPY orchestration/ orchestration/
COPY main.py wsgi.py cron_runner.py ./

# Copia frontend buildado
COPY --from=frontend-build /app/curadoria-web/dist curadoria-web/dist/

# Cria diretório de dados persistente
RUN mkdir -p /app/data /app/logs

# Instala cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Configura cron: seg, qua, sex às 10:00 UTC (07:00 BRT)
RUN echo "0 10 * * 1,3,5 cd /app && /usr/local/bin/python /app/cron_runner.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/curadoria-cron \
    && chmod 0644 /etc/cron.d/curadoria-cron \
    && crontab /etc/cron.d/curadoria-cron

# Script de inicialização
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
