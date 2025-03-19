FROM python:3.10-slim

WORKDIR /app

# Copier l'application Streamlit et les dépendances
COPY webapp/app.py webapp/requirements.txt /app/
# Copier le dossier commun, qui se trouve à la racine
COPY common /app/common

# Créer un environnement virtuel, mettre à jour pip et installer les dépendances
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["/venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
