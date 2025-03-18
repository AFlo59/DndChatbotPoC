import sqlite3
import json

conn = sqlite3.connect('dnd_game.db', check_same_thread=False)

# Création tables initiales
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.execute("""
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
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_context TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

def get_or_create_user(username, password=None, is_admin=False):
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user:
        return {"id": user[0], "username": user[1], "is_admin": bool(user[3])}
    conn.execute(
        "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
        (username, password, int(is_admin))
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return {"id": user[0], "username": user[1], "is_admin": bool(user[3])}

def register_user(username, password):
    existing_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if existing_user:
        return False
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password))
    conn.commit()
    return True

def authenticate_user(username, password):
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", 
        (username, password)).fetchone()
    return {"id": user[0], "username": user[1]} if user else None


def create_campaign(user_id, campaign_name, character_info, campaign_info):
    context = json.dumps({"history": []})
    conn.execute("""
    INSERT INTO campaigns (user_id, campaign_name, character_info, campaign_info, session_context)
    VALUES (?, ?, ?, ?, ?)""",
    (user_id, campaign_name, json.dumps(character_info), json.dumps(campaign_info), context))
    conn.commit()

def get_user_campaigns(user_id):
    campaigns = conn.execute("""
    SELECT id, campaign_name FROM campaigns WHERE user_id = ?""", (user_id,)).fetchall()
    return campaigns

def get_campaign(campaign_id):
    campaign = conn.execute("""
    SELECT * FROM campaigns WHERE id = ?""", (campaign_id,)).fetchone()
    return campaign

def update_campaign_context(campaign_id, session_context):
    conn.execute("""
    UPDATE campaigns SET session_context = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?""",
    (session_context, campaign_id))
    conn.commit()

def get_or_create_game_session(user_id):
    session = conn.execute(
        "SELECT * FROM game_sessions WHERE user_id = ?", (user_id,)
    ).fetchone()
    if session:
        return {"id": session[0], "user_id": session[1], "session_context": session[2]}
    conn.execute(
        "INSERT INTO game_sessions (user_id, session_context) VALUES (?, ?)", 
        (user_id, json.dumps({}))
    )
    conn.commit()
    session = conn.execute(
        "SELECT * FROM game_sessions WHERE user_id = ?", (user_id,)
    ).fetchone()
    return {"id": session[0], "user_id": session[1], "session_context": session[2]}

def update_game_session(session_id, context_json):
    conn.execute(
        "UPDATE game_sessions SET session_context = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
        (context_json, session_id)
    )
    conn.commit()
