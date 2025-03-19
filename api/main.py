# api/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
from typing import List, Dict, Any, Optional
import os
import sys

# Ajouter le répertoire parent au chemin pour pouvoir importer depuis common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.openai_api import OpenAIClient

app = FastAPI(
    title="DnD Chatbot API",
    description="API pour le chatbot D&D",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du client OpenAI
openai_client = None
try:
    openai_client = OpenAIClient()
except ValueError as e:
    print(f"Avertissement: {e}")
    print("Les fonctionnalités OpenAI ne seront pas disponibles.")

# Fonction pour obtenir une connexion à la base de données
def get_db():
    conn = sqlite3.connect("/data/dnd_game.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API du Chatbot D&D!"}

@app.get("/characters")
def get_all_characters(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM characters")
    characters = [dict(character) for character in cursor.fetchall()]
    return characters

@app.get("/characters/{character_id}")
def get_character(character_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    character = cursor.fetchone()
    
    if not character:
        raise HTTPException(status_code=404, detail="Personnage non trouvé")
    
    return dict(character)

@app.post("/characters")
def create_character(character: Dict[str, Any], db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Vérifier les champs requis
    required_fields = ["name", "race", "class"]
    for field in required_fields:
        if field not in character:
            raise HTTPException(status_code=400, detail=f"Le champ '{field}' est requis")
    
    # Préparer les champs et valeurs pour l'insertion
    fields = []
    values = []
    placeholders = []
    
    for key, value in character.items():
        fields.append(key)
        values.append(value)
        placeholders.append("?")
    
    # Construire et exécuter la requête d'insertion
    query = f"INSERT INTO characters ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
    cursor.execute(query, values)
    db.commit()
    
    # Récupérer l'ID du personnage créé
    character_id = cursor.lastrowid
    
    # Récupérer le personnage complet
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    created_character = dict(cursor.fetchone())
    
    return created_character

@app.get("/chat/{session_id}")
def get_chat_history(session_id: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Vérifier si la session existe
    cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session de chat non trouvée")
    
    # Récupérer les messages de la session
    cursor.execute("SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp", (session_id,))
    messages = [dict(message) for message in cursor.fetchall()]
    
    return messages

@app.post("/chat/{session_id}")
def add_chat_message(session_id: str, message: Dict[str, Any], db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Vérifier si la session existe, sinon la créer
    cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    
    if not session:
        # Créer une nouvelle session
        character_id = message.get("character_id")
        cursor.execute("INSERT INTO chat_sessions (id, character_id) VALUES (?, ?)", 
                      (session_id, character_id))
        db.commit()
    
    # Vérifier les champs requis pour le message
    if "role" not in message or "content" not in message:
        raise HTTPException(status_code=400, detail="Les champs 'role' et 'content' sont requis")
    
    # Insérer le message
    cursor.execute(
        "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, message["role"], message["content"])
    )
    db.commit()
    
    # Si le message est de l'utilisateur, générer une réponse avec OpenAI
    if message["role"] == "user" and openai_client:
        # Récupérer l'historique de la conversation
        cursor.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        chat_history = [{"role": msg["role"], "content": msg["content"]} for msg in cursor.fetchall()]
        
        # Générer une réponse
        try:
            response = openai_client.generate_response(chat_history)
            
            # Enregistrer la réponse dans la base de données
            cursor.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, "assistant", response)
            )
            db.commit()
            
            # Récupérer le message avec son ID
            cursor.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
                (session_id,)
            )
            assistant_message = dict(cursor.fetchone())
            
            return assistant_message
        except Exception as e:
            print(f"Erreur lors de la génération de réponse: {e}")
    
    # Récupérer le message avec son ID
    cursor.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,)
    )
    inserted_message = dict(cursor.fetchone())
    
    return inserted_message

@app.post("/generate/character-description")
def generate_character_description(character_info: Dict[str, Any]):
    if not openai_client:
        raise HTTPException(status_code=503, detail="Service OpenAI non disponible")
    
    try:
        description = openai_client.create_dnd_character_description(character_info)
        return {"description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")

@app.post("/generate/scenario")
def generate_scenario(context: Dict[str, Any]):
    if not openai_client:
        raise HTTPException(status_code=503, detail="Service OpenAI non disponible")
    
    try:
        scenario = openai_client.generate_dnd_scenario(context)
        return {"scenario": scenario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
