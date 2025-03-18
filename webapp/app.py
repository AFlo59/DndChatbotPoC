# ✅ Corrigé : webapp/app.py

import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("🧙 D&D Chatbot PoC")

# Session state initialisation
for key in ["authenticated", "user", "page", "selected_campaign"]:
    if key not in st.session_state:
        st.session_state[key] = None

def login_page():
    auth_action = st.sidebar.radio("Accès au jeu", ["Connexion", "Inscription"])

    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if st.sidebar.button(auth_action):
        endpoint = "/authenticate" if auth_action == "Connexion" else "/register"
        res = requests.post(f"{API_URL}/{auth_action.lower()}", json={"username": username, "password": password}).json()
        if res.get("id"):
            st.session_state.user = res
            st.session_state.page = "menu"
            st.rerun()
        else:
            st.sidebar.error("Erreur : " + res.get("error", "Inconnue"))


def menu_page():
    st.sidebar.success(f"Connecté : {st.session_state.user['username']}")

    action = st.sidebar.radio("Choix action", ["Reprendre une partie", "Créer une nouvelle partie"])

    if action == "Créer une nouvelle partie":
        campaign_name = st.sidebar.text_input("Nom de la campagne")
        char_name = st.sidebar.text_input("Nom du personnage")
        char_race = st.sidebar.selectbox("Race", ["Humain", "Elfe", "Nain", "Orc"])
        char_class = st.sidebar.selectbox("Classe", ["Guerrier", "Mage", "Rôdeur", "Voleur"])
        char_level = st.sidebar.number_input("Niveau initial", 1, 20, 1)
        campaign_desc = st.sidebar.text_area("Description campagne")

        if st.sidebar.button("Créer campagne"):
            res = requests.post(f"{API_URL}/campaign/create", json={
                "user_id": st.session_state.user['id'],
                "campaign_name": campaign_name,
                "character_info": {"name": char_name, "race": char_race, "class": char_class, "level": char_level},
                "campaign_info": {"description": campaign_desc}
            })
            if res.ok:
                st.session_state.selected_campaign = res.json()["campaign_id"]
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.sidebar.error("Erreur de création de campagne")


def chat_page():
    campaign = requests.get(f"{API_URL}/campaign/{st.session_state.selected_campaign}").json()
    session_context = campaign["session_context"]
    char_name = campaign["character_info"]["name"]

    st.subheader(f"🎲 Campagne : {campaign['campaign_name']}")

    chat_placeholder = st.container(height=400)
    with chat_placeholder:
        for msg in session_context["history"][-10:]:
            st.markdown(f"🧝 **{char_name}:** {msg['player']}")
            st.markdown(f"🧙 **DM:** {msg['dm']}")

    user_input = st.chat_input("Que fais-tu ?")

    if user_input:
        prompt = requests.post(f"{API_URL}/generate-prompt", json={"campaign_id": campaign['id'], "user_input": user_input}).json()
        response = requests.post(f"{API_URL}/generate_response", json={"prompt": prompt}).json()
        requests.post(f"{API_URL}/campaign/update", json={"campaign_id": campaign["id"], "user_input": user_input, "response": response})
        st.rerun()

    if st.sidebar.button("Retour au menu"):
        st.session_state.page = "menu"
        st.rerun()


def admin_page():
    logs = requests.get(f"{API_URL}/admin/logs", params={
        "admin_username": "adminuser",
        "admin_password": "adminpass123"
    }).json()

    st.header("🛡️ Admin Panel")

    for log in logs:
        st.markdown(f"**{log['user']} ({log['campaign']}):** {log['prompt']}")


# Contrôle clair des pages
if not st.session_state.user:
    login_page()
elif st.session_state.user['username'] == "adminuser":
    admin_page()
elif st.session_state.page == "menu":
    menu_page()
elif st.session_state.page == "chat":
    chat_page()
else:
    st.session_state.page = "menu"
    st.rerun()