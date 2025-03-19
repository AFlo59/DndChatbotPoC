FROM python:3.9-slim

WORKDIR /app

# Installer curl pour le healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .

# Créer un environnement virtuel
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

COPY api/main.py .
COPY common/ /app/common/

# Exposer le port sur lequel l'API va s'exécuter
EXPOSE 8000

# Commande pour démarrer l'API avec le venv
CMD ["/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
