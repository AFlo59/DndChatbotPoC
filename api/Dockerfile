FROM python:3.10-slim

WORKDIR /app

# Copier le code de l'API depuis le dossier "api" et le module commun depuis "common"
COPY api/main.py api/requirements.txt /app/
COPY common /app/common

# Créer un environnement virtuel, mettre à jour pip et installer les dépendances
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
