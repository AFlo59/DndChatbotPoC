# ✅ Corrigé : webapp/app.py

import streamlit as st
import requests
import uuid
import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au chemin pour pouvoir importer depuis common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database_api import DatabaseClient

# Initialisation du client pour l'API
api_url = os.getenv("API_URL", "http://api:8000")
db_client = DatabaseClient(api_url)

# Configuration de la page Streamlit
st.set_page_config(
    page_title="D&D Chatbot",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour initialiser les variables de session
def init_session_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "character_id" not in st.session_state:
        st.session_state.character_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "characters" not in st.session_state:
        try:
            st.session_state.characters = db_client.get_all_characters()
        except Exception as e:
            st.error(f"Erreur lors de la récupération des personnages: {e}")
            st.session_state.characters = []

# Initialiser les variables de session
init_session_state()

# Sidebar pour la sélection du personnage et les options
with st.sidebar:
    st.title("🐉 D&D Chatbot")
    st.subheader("Sélection du personnage")
    
    # Bouton pour rafraîchir la liste des personnages
    if st.button("Rafraîchir la liste"):
        try:
            st.session_state.characters = db_client.get_all_characters()
            st.success("Liste des personnages mise à jour!")
        except Exception as e:
            st.error(f"Erreur lors de la récupération des personnages: {e}")
    
    # Sélection du personnage
    character_options = ["Sélectionner un personnage..."] + [f"{char['name']} ({char['race']} {char['class']})" for char in st.session_state.characters]
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
    
    # Option pour créer un nouveau personnage
    st.subheader("Créer un nouveau personnage")
    if st.button("Nouveau personnage"):
        st.session_state.show_creation_form = True

# Formulaire de création de personnage
if st.session_state.get("show_creation_form", False):
    st.subheader("Créer un nouveau personnage")
    
    with st.form("character_creation"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nom")
            race = st.selectbox("Race", ["Humain", "Elfe", "Nain", "Halfelin", "Demi-Elfe", "Demi-Orc", "Gnome", "Tiefelin", "Dragonborn"])
            character_class = st.selectbox("Classe", ["Barbare", "Barde", "Clerc", "Druide", "Guerrier", "Moine", "Paladin", "Rôdeur", "Roublard", "Ensorceleur", "Sorcier", "Magicien"])
            level = st.number_input("Niveau", min_value=1, max_value=20, value=1)
        
        with col2:
            strength = st.slider("Force", min_value=3, max_value=18, value=10)
            dexterity = st.slider("Dextérité", min_value=3, max_value=18, value=10)
            constitution = st.slider("Constitution", min_value=3, max_value=18, value=10)
            intelligence = st.slider("Intelligence", min_value=3, max_value=18, value=10)
            wisdom = st.slider("Sagesse", min_value=3, max_value=18, value=10)
            charisma = st.slider("Charisme", min_value=3, max_value=18, value=10)
        
        background = st.text_area("Histoire du personnage")
        
        submitted = st.form_submit_button("Créer")
        
        if submitted:
            if not name:
                st.error("Le nom du personnage est requis!")
            else:
                # Créer le personnage via l'API
                character_data = {
                    "name": name,
                    "race": race,
                    "class": character_class,
                    "level": level,
                    "strength": strength,
                    "dexterity": dexterity,
                    "constitution": constitution,
                    "intelligence": intelligence,
                    "wisdom": wisdom,
                    "charisma": charisma,
                    "background": background
                }
                
                try:
                    new_character = db_client.create_character(character_data)
                    st.success(f"Personnage {name} créé avec succès!")
                    
                    # Mettre à jour la liste des personnages
                    st.session_state.characters = db_client.get_all_characters()
                    
                    # Sélectionner automatiquement le nouveau personnage
                    st.session_state.character_id = new_character["id"]
                    
                    # Masquer le formulaire
                    st.session_state.show_creation_form = False
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la création du personnage: {e}")

# Zone principale pour le chat
st.title("Chat avec le Maître du Jeu")

# Vérifier si un personnage est sélectionné
if not st.session_state.character_id:
    st.info("Veuillez sélectionner un personnage dans la barre latérale pour commencer à jouer.")
else:
    # Récupérer l'historique du chat si nécessaire
    if not st.session_state.messages:
        try:
            # Essayer de récupérer l'historique existant
            chat_history = db_client.get_chat_history(st.session_state.session_id)
            if chat_history:
                st.session_state.messages = chat_history
            else:
                # Initialiser avec un message système
                system_message = {
                    "role": "system",
                    "content": "Tu es un maître du jeu D&D qui guide les joueurs dans leur aventure."
                }
                db_client.add_chat_message(st.session_state.session_id, system_message)
                
                # Message de bienvenue du MJ
                welcome_message = {
                    "role": "assistant",
                    "content": "Bienvenue, aventurier! Je suis votre Maître du Jeu. Que souhaitez-vous faire aujourd'hui?"
                }
                db_client.add_chat_message(st.session_state.session_id, welcome_message)
                
                # Mettre à jour les messages locaux
                st.session_state.messages = db_client.get_chat_history(st.session_state.session_id)
        except Exception as e:
            st.error(f"Erreur lors de la récupération de l'historique: {e}")
            # Continuer avec un chat vide
            st.session_state.messages = []
    
    # Afficher les messages existants
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue  # Ne pas afficher les messages système
        
        if message["role"] == "user":
            st.chat_message("user", avatar="🧙‍♂️").write(message["content"])
        else:
            st.chat_message("assistant", avatar="🐉").write(message["content"])
    
    # Zone de saisie pour le nouveau message
    if prompt := st.chat_input("Que voulez-vous faire?"):
        # Afficher le message de l'utilisateur
        st.chat_message("user", avatar="🧙‍♂️").write(prompt)
        
        # Envoyer le message à l'API
        user_message = {
            "role": "user",
            "content": prompt,
            "character_id": st.session_state.character_id
        }
        
        try:
            # Envoyer le message et obtenir la réponse
            response = db_client.add_chat_message(st.session_state.session_id, user_message)
            
            # Afficher la réponse du MJ
            if response and response["role"] == "assistant":
                st.chat_message("assistant", avatar="🐉").write(response["content"])
                
                # Mettre à jour les messages locaux
                st.session_state.messages = db_client.get_chat_history(st.session_state.session_id)
        except Exception as e:
            st.error(f"Erreur lors de l'envoi du message: {e}")