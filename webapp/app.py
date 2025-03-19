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

# Utiliser le nom du service Docker au lieu de localhost
API_URL = os.getenv("API_URL", "http://api:8000")  # Le service s'appelle 'api' dans docker-compose

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
        
        # Si l'utilisateur n'est pas connecté, ne rien afficher
        if not st.session_state.user:
            return
        
        # Bouton déconnexion
        if st.button("Déconnexion"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            return
        
        # Bouton retour (sauf sur la page chat)
        if st.session_state.page != "chat":
            if st.button("← Retour"):
                st.session_state.page = "chat"
                st.rerun()
        
        # Si l'utilisateur est admin, afficher le menu admin
        if st.session_state.user.get('is_admin'):
            page = st.selectbox("Navigation", ["Chat", "Panel Admin"])
            if page == "Panel Admin":
                st.session_state.page = "admin"
                st.rerun()
            else:
                st.session_state.page = "chat"
        
        # Gestion des campagnes
        if st.session_state.page == "chat":
            st.subheader("Campagnes")
            
            try:
                res = requests.get(f"{API_URL}/campaigns/{st.session_state.user['id']}")
                if res.status_code == 200:
                    campaigns = res.json()
                    
                    if campaigns:
                        campaign_names = ["Sélectionner une campagne..."] + [
                            c['name'] for c in campaigns
                        ]
                        selected = st.selectbox("Vos campagnes", campaign_names)
                        
                        if selected != "Sélectionner une campagne...":
                            campaign = next(c for c in campaigns if c['name'] == selected)
                            if campaign != st.session_state.get('campaign'):
                                if st.button("Rejoindre cette campagne"):
                                    st.session_state.campaign = campaign
                                    st.session_state.character = None
                                    st.rerun()
                    
                    st.divider()
                    
                    if st.button("Créer une nouvelle campagne"):
                        st.session_state.campaign = None
                        st.session_state.character = None
                        st.session_state.page = "new_campaign"
                        st.rerun()
                else:
                    st.error("Erreur lors de la récupération des campagnes")
            except Exception as e:
                st.error(f"Erreur: {e}")

def new_campaign_page():
    st.title("🎲 Nouvelle Campagne")
    
    with st.form("campaign_form"):
        campaign_name = st.text_input("Nom de la campagne")
        campaign_desc = st.text_area("Description")
        submitted = st.form_submit_button("Créer")
        
        if submitted and campaign_name:
            try:
                res = requests.post(
                    f"{API_URL}/campaigns",
                    json={
                        "name": campaign_name,
                        "description": campaign_desc,
                        "user_id": st.session_state.user["id"]
                    }
                )
                
                if res.status_code == 200:
                    st.session_state.campaign = res.json()
                    st.session_state.page = "new_character"
                    st.rerun()
                else:
                    st.error(f"Erreur lors de la création: {res.text}")
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

    # Si pas de campagne, afficher un message
    if not st.session_state.campaign:
        st.info("👋 Bienvenue dans D&D Chatbot!")
        st.write("Pour commencer une partie, créez une nouvelle campagne ou sélectionnez-en une existante dans la barre latérale.")
        return

    st.title(f"🎲 Campagne: {st.session_state.campaign['name']}")
    
    # Vérifier si le personnage existe pour cette campagne
    try:
        res = requests.get(
            f"{API_URL}/characters/campaign/{st.session_state.campaign['id']}/user/{st.session_state.user['id']}"
        )
        if res.status_code == 200 and res.json():
            st.session_state.character = res.json()
            # Afficher l'interface de chat
            st.write(f"Jouant {st.session_state.character['name']}")
            # ... reste du code pour le chat ...
        else:
            st.warning("Vous devez d'abord créer votre personnage pour cette campagne.")
            st.session_state.page = "new_character"
            st.rerun()
    except Exception as e:
        st.error(f"Erreur lors de la récupération du personnage: {e}")

def character_creation_page():
    st.title("🧙‍♂️ Création de Personnage")
    st.write(f"Pour la campagne: {st.session_state.campaign['name']}")
    
    with st.form("character_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nom du personnage")
            race = st.selectbox("Race", [
                "Humain", "Elfe", "Nain", "Halfelin", "Gnome", 
                "Demi-Elfe", "Demi-Orc", "Tiefling", "Dragonborn"
            ])
            character_class = st.selectbox("Classe", [
                "Guerrier", "Magicien", "Voleur", "Clerc", "Ranger",
                "Paladin", "Barbare", "Barde", "Druide", "Moine", "Sorcier"
            ])
            level = st.number_input("Niveau", min_value=1, max_value=20, value=1)
        
        with col2:
            st.write("Caractéristiques")
            strength = st.slider("Force", min_value=8, max_value=18, value=10)
            dexterity = st.slider("Dextérité", min_value=8, max_value=18, value=10)
            constitution = st.slider("Constitution", min_value=8, max_value=18, value=10)
            intelligence = st.slider("Intelligence", min_value=8, max_value=18, value=10)
            wisdom = st.slider("Sagesse", min_value=8, max_value=18, value=10)
            charisma = st.slider("Charisme", min_value=8, max_value=18, value=10)
        
        background = st.text_area("Histoire du personnage", 
            help="Décrivez brièvement le passé de votre personnage")
        
        submitted = st.form_submit_button("Créer le personnage")
        
        if submitted and name:
            try:
                character_data = {
                    "name": name,
                    "race": race,
                    "class_name": character_class,
                    "campaign_id": st.session_state.campaign['id'],
                    "user_id": st.session_state.user['id'],
                    "level": level,
                    "strength": strength,
                    "dexterity": dexterity,
                    "constitution": constitution,
                    "intelligence": intelligence,
                    "wisdom": wisdom,
                    "charisma": charisma,
                    "background": background
                }
                
                res = requests.post(f"{API_URL}/characters", json=character_data)
                
                if res.status_code == 200:
                    st.session_state.character = res.json()
                    st.session_state.page = "chat"
                    st.rerun()
                else:
                    st.error(f"Erreur lors de la création: {res.text}")
            except Exception as e:
                st.error(f"Erreur: {e}")
        elif submitted:
            st.error("Veuillez au moins donner un nom à votre personnage")

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