# common/openai_api.py
import openai
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_game_prompt(context, user_input):
    prompt = f"""
    Tu es un Dungeon Master (DM) pour D&D.
    Contexte actuel: {context.get('history', [])}
    Le joueur dit: {user_input}.
    Réponds en décrivant clairement ce qui se passe ensuite.
    """
    return prompt.strip()

def get_gpt_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message["content"]

def generate_pixel_art(prompt):
    try:
        image_response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="256x256"
        )
        return image_response['data'][0]['url']
    except Exception as e:
        print(f"Erreur de génération d'image: {e}")
        return None

class OpenAIClient:
    """Fonctions pour interagir avec l'API OpenAI."""
    
    def __init__(self):
        """Initialise le client avec la clé API OpenAI."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans .env")
        openai.api_key = self.api_key

    def chat_completion(self, messages):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.8
            )
            return response.choices[0].message["content"]
        except Exception as e:
            raise Exception(f"Erreur OpenAI: {str(e)}")
    
    def generate_response(self, messages: List[Dict[str, str]], 
                        model: str = "gpt-3.5-turbo",
                        temperature: float = 0.7,
                        max_tokens: int = 1000) -> str:
        """
        Génère une réponse à partir d'une liste de messages.
        
        Args:
            messages: Liste de messages au format {"role": "user/assistant/system", "content": "texte"}
            model: Modèle OpenAI à utiliser
            temperature: Contrôle la créativité (0-1)
            max_tokens: Nombre maximum de tokens dans la réponse
            
        Returns:
            Le texte de la réponse générée
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message["content"]
        except Exception as e:
            print(f"Erreur lors de l'appel à OpenAI: {e}")
            return f"Désolé, une erreur s'est produite: {str(e)}"
    
    def create_dnd_character_description(self, character_info: Dict[str, Any]) -> str:
        """
        Crée une description narrative d'un personnage D&D.
        
        Args:
            character_info: Informations sur le personnage (race, classe, etc.)
            
        Returns:
            Description narrative du personnage
        """
        prompt = f"""
        Crée une description narrative pour un personnage D&D avec les caractéristiques suivantes:
        - Nom: {character_info.get('name', 'Inconnu')}
        - Race: {character_info.get('race', 'Humain')}
        - Classe: {character_info.get('class', 'Guerrier')}
        - Niveau: {character_info.get('level', 1)}
        - Force: {character_info.get('strength', 10)}
        - Dextérité: {character_info.get('dexterity', 10)}
        - Constitution: {character_info.get('constitution', 10)}
        - Intelligence: {character_info.get('intelligence', 10)}
        - Sagesse: {character_info.get('wisdom', 10)}
        - Charisme: {character_info.get('charisma', 10)}
        - Histoire: {character_info.get('background', 'Aucune information disponible')}
        """
        
        messages = [
            {"role": "system", "content": "Tu es un maître du jeu D&D expert qui crée des descriptions de personnages vivantes et immersives."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat_completion(messages)
    
    def generate_dnd_scenario(self, context: Dict[str, Any]) -> str:
        """
        Génère un scénario D&D basé sur le contexte fourni.
        
        Args:
            context: Informations contextuelles pour le scénario
            
        Returns:
            Scénario généré
        """
        prompt = f"""
        Génère un scénario D&D avec les éléments suivants:
        - Environnement: {context.get('environment', 'Donjon')}
        - Niveau des personnages: {context.get('level', '1-5')}
        - Type d'aventure: {context.get('adventure_type', 'Exploration')}
        - Thème: {context.get('theme', 'Fantasy classique')}
        - Antagoniste principal: {context.get('antagonist', 'Un nécromancien')}
        """
        
        messages = [
            {"role": "system", "content": "Tu es un maître du jeu D&D expert qui crée des scénarios captivants et équilibrés."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat_completion(messages)
