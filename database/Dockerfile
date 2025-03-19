# database/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Installer curl pour le healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY init_db.py .

# sqlite3 est déjà inclus dans Python, pas besoin de l'installer
RUN pip install --no-cache-dir python-dotenv

# Le CMD est maintenant géré par docker-compose

