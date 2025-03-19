# database/init_db.py
import sqlite3
import os
from dotenv import load_dotenv

# Charge `.env` à partir de la racine
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

# Récupérer les credentials admin depuis .env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Vérifier et créer le dossier database/ s'il n'existe pas
db_path = "database/dnd_game.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connexion à la base de données
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Création des tables si elles n'existent pas déjà
cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    campaign_name TEXT,
    character_info TEXT,  -- JSON infos personnage
    campaign_info TEXT,   -- JSON contexte initial
    session_context TEXT, -- Historique complet
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_context TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

# Insertion de l'admin par défaut si non existant
cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
admin_user = cursor.fetchone()

if not admin_user:
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                   (ADMIN_USERNAME, ADMIN_PASSWORD, 1))
    print(f"Superuser '{ADMIN_USERNAME}' ajouté avec succès.")

# Sauvegarde et fermeture de la connexion
conn.commit()
conn.close()

print("Base de données initialisée avec succès.")
