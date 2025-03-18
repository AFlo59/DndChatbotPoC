import streamlit as st
import database as db
import openai_api as ai
import json, os
from dotenv import load_dotenv

load_dotenv()

st.title("🧙 D&D Chatbot PoC")

# Session state initialisation
for key in ["authenticated", "user", "page", "selected_campaign"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Fonctions claires de gestion de pages
def login_page():
    auth_action = st.sidebar.radio("Accès au jeu", ["Connexion", "Inscription"])

    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if st.sidebar.button(auth_action):
        if auth_action == "Connexion":
            user = db.authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.session_state.authenticated = True
                st.session_state.page = "menu"
                st.rerun()
            else:
                st.sidebar.error("Identifiants invalides !")
        elif auth_action == "Inscription":
            created = db.register_user(username, password)
            if created:
                st.sidebar.success("Compte créé ! Connecte-toi maintenant.")
            else:
                st.sidebar.error("Ce nom d'utilisateur existe déjà.")

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
            character_info = {
                "name": char_name,
                "race": char_race,
                "class": char_class,
                "level": char_level
            }
            campaign_info = {"description": campaign_desc}
            db.create_campaign(st.session_state.user['id'], campaign_name, character_info, campaign_info)
            campaigns = db.get_user_campaigns(st.session_state.user['id'])
            st.session_state.selected_campaign = campaigns[-1][0]
            st.session_state.page = "chat"
            st.rerun()

    elif action == "Reprendre une partie":
        campaigns = db.get_user_campaigns(st.session_state.user['id'])
        if campaigns:
            campaign_dict = {name: cid for cid, name in campaigns}
            selected_campaign_name = st.sidebar.selectbox("Ta campagne", campaign_dict.keys())
            st.session_state.selected_campaign = campaign_dict[selected_campaign_name]
            if st.sidebar.button("Continuer"):
                st.session_state.page = "chat"
                st.rerun()
        else:
            st.sidebar.warning("Aucune campagne trouvée, crée une nouvelle partie.")

def chat_page():
    campaign = db.get_campaign(st.session_state.selected_campaign)
    session_context = json.loads(campaign[5])
    char_info = json.loads(campaign[3])
    char_name = char_info["name"]

    st.subheader(f"🎲 Campagne : {campaign[2]}")

    chat_placeholder = st.container(height=400)
    with chat_placeholder:
        for msg in session_context["history"][-10:]:
            st.markdown(f"🧝 **{char_name}:** {msg['player']}")
            st.markdown(f"🧙 **DM:** {msg['dm']}")

    user_input = st.chat_input("Que fais-tu ?")

    if user_input:
        prompt = ai.generate_game_prompt(session_context, user_input)
        response = ai.get_gpt_response(prompt)

        session_context["history"].append({"player": user_input, "dm": response})
        db.update_campaign_context(campaign[0], json.dumps(session_context))
        st.rerun()

    if st.sidebar.button("Retour au menu"):
        st.session_state.page = "menu"
        st.rerun()

# Contrôle clair de la navigation des pages
if not st.session_state.authenticated:
    login_page()
elif st.session_state.page == "menu":
    menu_page()
elif st.session_state.page == "chat":
    chat_page()
else:
    st.session_state.page = "menu"
    st.rerun()