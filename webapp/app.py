# ✅ Corrigé : webapp/app.py

import streamlit as st
import requests
import uuid
import os
import sys
from datetime import datetime
import pandas as pd

# Ajouter le répertoire parent au chemin pour pouvoir importer depuis common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database_api import DatabaseClient

# Utiliser le nom du service Docker au lieu de localhost
API_URL = os.getenv("API_URL", "http://api:8000")  # Le service s'appelle 'api' dans docker-compose

# Initialisation du client pour l'API
db_client = DatabaseClient(API_URL)

# Configuration de la page Streamlit
st.set_page_config(
    page_title="D&D Chatbot",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour initialiser les variables de session
def init_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "user" not in st.session_state:
        st.session_state.user = None
    if "campaign" not in st.session_state:
        st.session_state.campaign = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "character_id" not in st.session_state:
        st.session_state.character_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "characters" not in st.session_state:
        st.session_state.characters = []

# Initialiser l'état de session
init_session_state()

def sidebar_content():
    """Gère le contenu de la sidebar en fonction de l'état de connexion"""
    with st.sidebar:
        st.title("🐉 D&D Chatbot")
        
        if not st.session_state.user:
            return
        
        if st.session_state.user.get('is_admin'):
            page = st.selectbox("Navigation", ["Chat", "Panel Admin"])
            if page == "Panel Admin":
                st.session_state.page = "admin"
                st.rerun()
            else:
                st.session_state.page = "chat"
        
        if st.session_state.page == "chat":
            if not st.session_state.campaign:
                st.subheader("Nouvelle Campagne")
                if st.button("Créer une campagne"):
                    st.session_state.page = "new_campaign"
                    st.rerun()
            else:
                st.subheader("Sélection du personnage")
                if st.button("Rafraîchir la liste"):
                    try:
                        st.session_state.characters = db_client.get_all_characters()
                        st.success("Liste mise à jour!")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
                
                if st.session_state.characters:
                    character_options = ["Sélectionner..."] + [
                        f"{char['name']} ({char['race']} {char['class']})" 
                        for char in st.session_state.characters
                    ]
                    selected = st.selectbox("Personnage", character_options)
                    
                    if selected != "Sélectionner...":
                        idx = character_options.index(selected) - 1
                        show_character_details(st.session_state.characters[idx])
                
                if st.button("Nouveau personnage"):
                    st.session_state.page = "new_character"
                    st.rerun()

def new_campaign_page():
    st.title("🎲 Nouvelle Campagne")
    
    with st.form("campaign_form"):
        campaign_name = st.text_input("Nom de la campagne")
        campaign_desc = st.text_area("Description")
        submitted = st.form_submit_button("Créer")
        
        if submitted and campaign_name:
            try:
                campaign = db_client.create_campaign({
                    "name": campaign_name,
                    "description": campaign_desc,
                    "user_id": st.session_state.user["id"]
                })
                st.session_state.campaign = campaign
                st.session_state.page = "new_character"
                st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")

def login_page():
    st.title("🎲 Connexion D&D Chatbot")
    
    auth_action = st.radio("Accès au jeu", ["Connexion", "Inscription"])
    
    with st.form(key="auth_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button(auth_action)
        
        if submit and username and password:  # Vérifier que les champs ne sont pas vides
            try:
                endpoint = "authenticate" if auth_action == "Connexion" else "register"
                res = requests.post(
                    f"{API_URL}/{endpoint}",
                    json={"username": username, "password": password},
                    timeout=10
                )
                
                if res.status_code == 200:
                    data = res.json()
                    if data.get("id"):
                        st.session_state.user = data
                        st.session_state.page = "chat"
                        st.rerun()
                    else:
                        st.error("Échec de l'authentification")
                elif res.status_code == 400 and "déjà pris" in res.json().get("detail", ""):
                    st.error("Ce nom d'utilisateur est déjà utilisé")
                else:
                    st.error(f"Erreur {res.status_code}: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de connexion: {str(e)}")
                st.info(f"Tentative de connexion à {API_URL}")
        elif submit:
            st.error("Veuillez remplir tous les champs")

def admin_page():
    st.title("🛡️ Panel Administrateur")
    
    # Vérifier que l'utilisateur est admin
    if not st.session_state.user.get('is_admin'):
        st.error("Accès non autorisé")
        return
    
    # Tabs pour différentes sections
    tab1, tab2, tab3 = st.tabs(["Utilisateurs", "Historique des chats", "Statistiques"])
    
    with tab1:
        st.header("Liste des utilisateurs")
        try:
            headers = {"Authorization": f"Bearer {st.session_state.user['id']}"}
            response = requests.get(f"{API_URL}/admin/users", headers=headers)
            users = response.json()
            
            # Afficher les utilisateurs dans un tableau
            if users:
                df = pd.DataFrame(users)
                st.dataframe(df)
            else:
                st.info("Aucun utilisateur trouvé")
        except Exception as e:
            st.error(f"Erreur lors de la récupération des utilisateurs: {e}")
    
    with tab2:
        st.header("Historique des chats")
        try:
            headers = {"Authorization": f"Bearer {st.session_state.user['id']}"}
            response = requests.get(f"{API_URL}/admin/chat-history", headers=headers)
            messages = response.json()
            
            if messages:
                df = pd.DataFrame(messages)
                st.dataframe(df)
            else:
                st.info("Aucun message trouvé")
        except Exception as e:
            st.error(f"Erreur lors de la récupération de l'historique: {e}")
    
    with tab3:
        st.header("Statistiques globales")
        try:
            headers = {"Authorization": f"Bearer {st.session_state.user['id']}"}
            response = requests.get(f"{API_URL}/admin/stats", headers=headers)
            stats = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Utilisateurs", stats['total_users'])
            with col2:
                st.metric("Personnages", stats['total_characters'])
            with col3:
                st.metric("Messages", stats['total_messages'])
            
            # Graphique des messages par jour
            if stats['daily_messages']:
                df = pd.DataFrame(stats['daily_messages'])
                st.line_chart(df.set_index('date')['count'])
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des statistiques: {e}")

def chat_page():
    if not st.session_state.user:
        st.warning("Veuillez vous connecter pour accéder au chat.")
        st.session_state.page = "login"
        st.rerun()
        return

    st.title("🐉 D&D Chatbot")
    
    # Sidebar pour la sélection du personnage et les options
    with st.sidebar:
        st.subheader("Sélection du personnage")
        
        # Bouton pour rafraîchir la liste des personnages
        if st.button("Rafraîchir la liste"):
            try:
                st.session_state.characters = db_client.get_all_characters()
                st.success("Liste des personnages mise à jour!")
            except Exception as e:
                st.error(f"Erreur lors de la récupération des personnages: {e}")
        
        # Sélection du personnage
        character_options = ["Sélectionner un personnage..."] + [
            f"{char['name']} ({char['race']} {char['class']})" 
            for char in st.session_state.characters
        ]
        selected_character = st.selectbox("Choisir un personnage", character_options)
        
        if selected_character != "Sélectionner un personnage...":
            # Trouver l'ID du personnage sélectionné
            selected_index = character_options.index(selected_character) - 1  # -1 pour compenser l'option par défaut
            st.session_state.character_id = st.session_state.characters[selected_index]["id"]
            
            # Afficher les détails du personnage
            character = st.session_state.characters[selected_index]
            st.subheader("Détails du personnage")
            st.write(f"**Niveau:** {character['level']}")
            st.write(f"**Force:** {character['strength']}")
            st.write(f"**Dextérité:** {character['dexterity']}")
            st.write(f"**Constitution:** {character['constitution']}")
            st.write(f"**Intelligence:** {character['intelligence']}")
            st.write(f"**Sagesse:** {character['wisdom']}")
            st.write(f"**Charisme:** {character['charisma']}")
            
            if "background" in character and character["background"]:
                st.write("**Histoire:**")
                st.write(character["background"])

# À la fin du fichier
sidebar_content()

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "new_campaign":
    new_campaign_page()
elif st.session_state.page == "new_character":
    if not st.session_state.campaign:
        st.warning("Veuillez d'abord créer une campagne")
        st.session_state.page = "new_campaign"
        st.rerun()
    else:
        character_creation_page()
elif st.session_state.page == "admin" and st.session_state.user.get('is_admin'):
    admin_page()
elif st.session_state.page == "chat":
    chat_page()
else:
    st.session_state.page = "login"
    st.rerun()