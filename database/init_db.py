# database/init_db.py
import sqlite3
import os
from dotenv import load_dotenv
import hashlib

# Charge `.env` à partir de la racine
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

def init_db():
    # Créer le dossier data s'il n'existe pas
    if not os.path.exists('/data'):
        os.makedirs('/data')
    
    # Se connecter à la base de données
    conn = sqlite3.connect('/data/dnd_game.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Créer les tables
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
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

    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        race TEXT NOT NULL,
        class_name TEXT NOT NULL,
        level INTEGER DEFAULT 1,
        campaign_id INTEGER,
        user_id INTEGER,
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
        FOREIGN KEY (character_id) REFERENCES characters(id)
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
    );
    ''')

    # Récupérer les credentials depuis .env
    admin_username = os.getenv('ADMIN_USERNAME', 'adminuser')
    admin_password = os.getenv('ADMIN_PASSWORD', 'adminpass')
    user_username = os.getenv('USER_USERNAME', 'testuser')
    user_password = os.getenv('USER_PASSWORD', 'testpass')

    # Hasher les mots de passe
    admin_password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    user_password_hash = hashlib.sha256(user_password.encode()).hexdigest()

    # Ajouter l'admin s'il n'existe pas
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password, is_admin)
    VALUES (?, ?, TRUE)
    ''', (admin_username, admin_password_hash))

    # Ajouter l'utilisateur test s'il n'existe pas
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password, is_admin)
    VALUES (?, ?, FALSE)
    ''', (user_username, user_password_hash))

    # Ajouter des données d'exemple si la base est vide
    cursor.execute("SELECT COUNT(*) FROM characters")
    if cursor.fetchone()[0] == 0:
        # Ajouter quelques personnages d'exemple
        cursor.execute('''
        INSERT INTO characters (name, race, class_name, level, strength, dexterity, constitution, intelligence, wisdom, charisma, background)
        VALUES 
        ('Thorin', 'Nain', 'Guerrier', 5, 16, 12, 14, 10, 8, 10, 'Ancien soldat devenu mercenaire après la chute de son royaume.'),
        ('Elindra', 'Elfe', 'Magicienne', 4, 8, 14, 10, 16, 12, 14, 'Érudite de la tour d''Argent, spécialiste des arts arcanes.'),
        ('Grog', 'Demi-Orc', 'Barbare', 3, 18, 12, 16, 8, 10, 8, 'Élevé par une tribu nomade, cherche à prouver sa valeur.')
        ''')

    conn.commit()
    conn.close()

    print("Base de données initialisée avec succès.")

if __name__ == '__main__':
    init_db()
    print(f"Superuser '{os.getenv('ADMIN_USERNAME')}' ajouté avec succès.")
