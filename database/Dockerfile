# database/Dockerfile
FROM alpine:latest

# Installer sqlite, Python3 et pip
RUN apk add --no-cache sqlite python3 py3-pip

# Créer un environnement virtuel
RUN python3 -m venv /venv

# Mettre à jour pip dans l'environnement virtuel
RUN /venv/bin/pip install --upgrade pip

# Installer python-dotenv dans le virtualenv
RUN /venv/bin/pip install python-dotenv

WORKDIR /database
COPY init_db.py /init_db.py

# Utiliser le python du virtualenv pour lancer le script
CMD ["/venv/bin/python", "/init_db.py"]

