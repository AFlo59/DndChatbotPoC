# Utilisation d'une image Python légère
FROM python:3.10-slim

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires
COPY main.py requirements.txt /app/

# Créer un environnement virtuel, mettre à jour pip et installer les dépendances
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Lancer l'API avec Uvicorn en utilisant l'interpréteur du virtualenv
CMD ["/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]