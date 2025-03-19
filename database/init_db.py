# database/init_db.py
import sqlite3
import os
from dotenv import load_dotenv
import hashlib

# Charge `.env` à partir de la racine
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

# Récupérer les credentials admin depuis .env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Vérifier et créer le dossier database/ s'il n'existe pas
db_path = "data/dnd_game.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connexion à la base de données
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Création des tables si elles n'existent pas déjà
cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_context TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    race TEXT NOT NULL,
    class TEXT NOT NULL,
    campaign_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    level INTEGER DEFAULT 1,
    strength INTEGER DEFAULT 10,
    dexterity INTEGER DEFAULT 10,
    constitution INTEGER DEFAULT 10,
    intelligence INTEGER DEFAULT 10,
    wisdom INTEGER DEFAULT 10,
    charisma INTEGER DEFAULT 10,
    background TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    character_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters (id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
);
""")

# Insertion de l'admin par défaut si non existant
cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
admin_user = cursor.fetchone()

if not admin_user:
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                   (ADMIN_USERNAME, ADMIN_PASSWORD, 1))
    print(f"Superuser '{ADMIN_USERNAME}' ajouté avec succès.")

# Insertion de l'utilisateur test si non existant
cursor.execute("SELECT * FROM users WHERE username = ?", (os.getenv("USER_USERNAME"),))
test_user = cursor.fetchone()

if not test_user:
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (os.getenv("USER_USERNAME"), hashlib.sha256(os.getenv("USER_PASSWORD").encode()).hexdigest())
    )

# Si la base de données vient d'être créée, ajouter des données d'exemple
if not os.path.exists(db_path):
    # Ajouter quelques personnages d'exemple
    cursor.execute('''
    INSERT INTO characters (name, race, class, level, strength, dexterity, constitution, intelligence, wisdom, charisma, background)
    VALUES 
    ('Thorin', 'Nain', 'Guerrier', 5, 16, 12, 14, 10, 8, 10, 'Ancien soldat devenu mercenaire après la chute de son royaume.'),
    ('Elindra', 'Elfe', 'Magicienne', 4, 8, 14, 10, 16, 12, 14, 'Érudite de la tour d''Argent, spécialiste des arts arcanes.'),
    ('Grog', 'Demi-Orc', 'Barbare', 3, 18, 12, 16, 8, 10, 8, 'Élevé par une tribu nomade, cherche à prouver sa valeur.')
    ''')
    
    # Ajouter une session de chat d'exemple
    cursor.execute('''
    INSERT INTO chat_sessions (id, character_id)
    VALUES ('session_exemple', 1)
    ''')
    
    # Ajouter quelques messages d'exemple
    cursor.execute('''
    INSERT INTO chat_messages (session_id, role, content)
    VALUES 
    ('session_exemple', 'system', 'Tu es un maître du jeu D&D qui guide les joueurs dans leur aventure.'),
    ('session_exemple', 'user', 'Je voudrais explorer la forêt enchantée.'),
    ('session_exemple', 'assistant', 'Alors que tu t''enfonces dans la forêt enchantée, les arbres semblent s''animer autour de toi. Au loin, tu aperçois une lueur bleutée qui scintille entre les branches. Que souhaites-tu faire ?')
    ''')

# Sauvegarde et fermeture de la connexion
conn.commit()
conn.close()

print("Base de données initialisée avec succès.")
