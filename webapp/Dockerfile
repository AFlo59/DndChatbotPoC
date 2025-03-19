FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY webapp/requirements.txt .

# Installer d'abord numpy
RUN pip install --no-cache-dir numpy==1.23.5

# Puis installer le reste des dépendances
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp/app.py .
COPY common/ /app/common/

# Exposer le port sur lequel Streamlit va s'exécuter
EXPOSE 8502

# Commande pour démarrer l'application Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "8502", "--server.address", "0.0.0.0"]
