# api/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uuid
from typing import List, Dict, Any, Optional
import os
import sys
import hashlib
from datetime import datetime
from contextlib import contextmanager
import threading

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
@contextmanager
def get_db():
    """Crée une nouvelle connexion pour chaque requête"""
    conn = sqlite3.connect("/data/dnd_game.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Modèles Pydantic pour l'authentification
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime

class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime
    username: Optional[str]

class Campaign(BaseModel):
    name: str
    description: str
    user_id: int

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API du Chatbot D&D!"}

@app.get("/characters")
async def get_all_characters():
    with get_db() as db:
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
async def create_character(character: dict):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO characters (name, race, class, level, strength, dexterity, 
                                  constitution, intelligence, wisdom, charisma, background)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            character["name"], character["race"], character["class"], character["level"],
            character["strength"], character["dexterity"], character["constitution"],
            character["intelligence"], character["wisdom"], character["charisma"],
            character.get("background", "")
        ))
        db.commit()
        return {"id": cursor.lastrowid, **character}

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

# Fonction utilitaire pour hacher les mots de passe
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/register")
async def register(user: UserCreate):
    hashed_password = hash_password(user.password)
    
    with get_db() as db:
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                (user.username, hashed_password, False)
            )
            db.commit()
            
            # Récupérer l'utilisateur créé
            cursor.execute(
                "SELECT id, username, is_admin FROM users WHERE username = ?",
                (user.username,)
            )
            user_data = cursor.fetchone()
            return {
                "id": user_data[0],
                "username": user_data[1],
                "is_admin": bool(user_data[2])
            }
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà pris")

@app.post("/authenticate")
async def login(user: UserLogin):
    hashed_password = hash_password(user.password)
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, username, is_admin FROM users WHERE username = ? AND password = ?",
            (user.username, hashed_password)
        )
        user_data = cursor.fetchone()
    
    if user_data is None:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    return {
        "id": user_data[0],
        "username": user_data[1],
        "is_admin": bool(user_data[2])
    }

@app.get("/admin/users", response_model=List[UserResponse])
async def get_users(db: sqlite3.Connection = Depends(get_db)):
    """Liste tous les utilisateurs (admin uniquement)"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, username, is_admin, created_at 
        FROM users
        ORDER BY created_at DESC
    """)
    users = [dict(row) for row in cursor.fetchall()]
    return users

@app.get("/admin/chat-history", response_model=List[ChatMessageResponse])
async def get_all_chat_history(
    db: sqlite3.Connection = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Récupère l'historique complet des chats (admin uniquement)"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            cm.id,
            cm.session_id,
            cm.role,
            cm.content,
            cm.timestamp,
            u.username
        FROM chat_messages cm
        LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
        LEFT JOIN characters c ON cs.character_id = c.id
        LEFT JOIN users u ON u.id = c.id
        ORDER BY cm.timestamp DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    messages = [dict(row) for row in cursor.fetchall()]
    return messages

@app.get("/admin/stats")
async def get_stats(db: sqlite3.Connection = Depends(get_db)):
    """Récupère les statistiques globales (admin uniquement)"""
    cursor = db.cursor()
    
    # Nombre total d'utilisateurs
    cursor.execute("SELECT COUNT(*) as user_count FROM users")
    user_count = cursor.fetchone()['user_count']
    
    # Nombre total de personnages
    cursor.execute("SELECT COUNT(*) as character_count FROM characters")
    character_count = cursor.fetchone()['character_count']
    
    # Nombre total de messages
    cursor.execute("SELECT COUNT(*) as message_count FROM chat_messages")
    message_count = cursor.fetchone()['message_count']
    
    # Messages par jour (7 derniers jours)
    cursor.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM chat_messages
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """)
    daily_messages = [dict(row) for row in cursor.fetchall()]
    
    return {
        "total_users": user_count,
        "total_characters": character_count,
        "total_messages": message_count,
        "daily_messages": daily_messages
    }

# Middleware pour vérifier les droits admin
def admin_required(db: sqlite3.Connection = Depends(get_db)):
    async def check_admin(request):
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        try:
            # Format attendu: "Bearer user_id"
            user_id = int(auth.split(" ")[1])
            cursor = db.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user or not user['is_admin']:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            
            return user_id
        except (IndexError, ValueError):
            raise HTTPException(status_code=401, detail="Token invalide")
    
    return check_admin

@app.post("/campaigns")
async def create_campaign(campaign: Campaign):
    with get_db() as db:
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO campaigns (name, description, user_id)
                VALUES (?, ?, ?)
            """, (campaign.name, campaign.description, campaign.user_id))
            db.commit()
            
            campaign_id = cursor.lastrowid
            return {
                "id": campaign_id,
                "name": campaign.name,
                "description": campaign.description,
                "user_id": campaign.user_id
            }
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Erreur de base de données: {str(e)}")

@app.get("/campaigns/{user_id}")
async def get_user_campaigns(user_id: int):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, description, created_at 
            FROM campaigns 
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        campaigns = [dict(row) for row in cursor.fetchall()]
        return campaigns

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
