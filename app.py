import streamlit as st
import database as db
import openai_api as ai
import json, os
from dotenv import load_dotenv

load_dotenv()

st.title("🧙 D&D Chatbot PoC")

# Authentification utilisateur
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")

if username and password:
    if (username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD")):
        user = db.get_or_create_user(username, password, is_admin=True)
    elif (username == os.getenv("USER_USERNAME") and password == os.getenv("USER_PASSWORD")):
        user = db.get_or_create_user(username, password)
    else:
        st.sidebar.error("Identifiants incorrects.")
        user = None
else:
    user = None

if user:
    st.sidebar.success(f"Connecté: {user['username']}")

    # Choix créer ou reprendre une campagne
    action = st.sidebar.radio("Que veux-tu faire ?", ["Reprendre une partie", "Créer une nouvelle partie"])

    if action == "Créer une nouvelle partie":
        campaign_name = st.sidebar.text_input("Nom de la campagne")
        char_name = st.sidebar.text_input("Nom du personnage")
        char_race = st.sidebar.selectbox("Race du personnage", ["Humain", "Elfe", "Nain", "Orc"])
        char_class = st.sidebar.selectbox("Classe du personnage", ["Guerrier", "Mage", "Rôdeur", "Voleur"])
        char_level = st.sidebar.number_input("Niveau initial", min_value=1, max_value=20, value=1)
        campaign_desc = st.sidebar.text_area("Description initiale de la campagne")

        if st.sidebar.button("Créer la campagne"):
            character_info = {
                "name": char_name,
                "race": char_race,
                "class": char_class,
                "level": char_level
            }
            campaign_info = {"description": campaign_desc}
            db.create_campaign(user['id'], campaign_name, character_info, campaign_info)
            st.sidebar.success("Campagne créée avec succès !")

    elif action == "Reprendre une partie":
        campaigns = db.get_user_campaigns(user['id'])
        campaign_dict = {name: cid for cid, name in campaigns}
        selected_campaign_name = st.sidebar.selectbox("Sélectionne ta campagne", campaign_dict.keys())

        campaign = db.get_campaign(campaign_dict[selected_campaign_name])
        session_context = json.loads(campaign[5])

        # Affichage de l'historique du chat
        st.subheader(f"Campagne : {selected_campaign_name}")
        chat_placeholder = st.container(height=400)
        with chat_placeholder:
            for msg in session_context["history"]:
                st.markdown(f"🧝 **Toi:** {msg['player']}")
                st.markdown(f"🧙 **DM:** {msg['dm']}")

        # Input fixé en bas
        user_input = st.chat_input("Que fais-tu ?")

        if user_input:
            prompt = ai.generate_game_prompt(session_context, user_input)
            response = ai.get_gpt_response(prompt)

            # Mise à jour contexte et sauvegarde
            session_context["history"].append({"player": user_input, "dm": response})
            db.update_campaign_context(campaign[0], json.dumps(session_context))

            # Rafraîchir immédiatement le chat
            st.rerun()

