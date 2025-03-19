# api/main.py
from fastapi import FastAPI, HTTPException
from common.database_api import (
    authenticate_user,
    register_user,
    create_campaign,
    fetch_campaign as get_campaign,
    update_campaign as update_campaign_context,
    get_all_campaign_logs
)
from common.openai_api import generate_game_prompt, get_gpt_response
import json
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

app = FastAPI()

@app.post("/authenticate")
def authenticate(username: str, password: str):
    return authenticate_user(username, password)

@app.post("/register")
def register(username: str, password: str):
    return register_user(username, password)

@app.post("/campaign/create")
def create_campaign_endpoint(user_id:int, campaign_name:str, character_info:dict, campaign_info:dict):
    return create_campaign(user_id, campaign_name, character_info, campaign_info)

@app.get("/campaign/{campaign_id}")
def fetch_campaign(campaign_id: int):
    return get_campaign(campaign_id)

@app.post("/campaign/update")
def update_campaign(campaign_id: int, session_context: dict):
    return update_campaign_context(campaign_id, json.dumps(session_context))

# 🔹 Récupérer les logs admin
@app.get("/admin/logs")
def get_logs(admin_username:str, admin_password:str):
    admin = authenticate_user(admin_username, admin_password)
    if admin and "is_admin" in admin and admin["is_admin"]:
        return get_all_campaign_logs()
    else:
        raise HTTPException(status_code=403, detail="Accès interdit")
