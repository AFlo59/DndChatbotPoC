FROM python:3.10-slim

WORKDIR /app

# Copier les fichiers de l'application
COPY app.py database_api.py openai_api.py requirements.txt /app/

# Créer un environnement virtuel, mettre à jour pip et installer les dépendances
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# Utiliser l'interpréteur du virtualenv pour lancer Streamlit
CMD ["/venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
