import requests
import os
import json
from dotenv import load_dotenv

# Charger `.env` depuis la racine
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_all_campaign_logs():
    """Récupère tous les logs de campagnes depuis l'API (pour admin)."""
    res = requests.get(f"{API_URL}/admin/logs")
    if res.status_code == 200:
        return res.json()
    else:
        print(f"Erreur API logs : {res.status_code}, {res.text}")
        return None

def authenticate_user(username, password):
    """Authentifie un utilisateur via l'API."""
    res = requests.post(f"{API_URL}/authenticate", json={"username": username, "password": password})
    return res.json() if res.status_code == 200 else None

def register_user(username, password):
    """Crée un nouvel utilisateur."""
    res = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
    return res.status_code == 200

def create_campaign(user_id, campaign_name, character_info, campaign_info):
    """Crée une campagne pour un utilisateur."""
    res = requests.post(f"{API_URL}/campaign/create", json={
        "user_id": user_id,
        "campaign_name": campaign_name,
        "character_info": character_info,
        "campaign_info": campaign_info
    })
    if res.status_code == 200:
        return res.json()
    else:
        print(f"Erreur création campagne : {res.status_code}, {res.text}")
        return None

def fetch_campaign(campaign_id):
    """Récupère les détails d'une campagne."""
    res = requests.get(f"{API_URL}/campaign/{campaign_id}")
    if res.status_code == 200:
        return res.json()
    else:
        print(f"Erreur récupération campagne : {res.status_code}, {res.text}")
        return None

def update_campaign(campaign_id, session_context):
    """Met à jour le contexte d'une campagne."""
    res = requests.post(f"{API_URL}/campaign/update", json={
        "campaign_id": campaign_id,
        "session_context": session_context
    })
    if res.status_code == 200:
        return True
    else:
        print(f"Erreur mise à jour campagne : {res.status_code}, {res.text}")
        return False
