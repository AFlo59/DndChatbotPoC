DndChatbotPoC/
├── docker-compose.yml         # Orchestration de vos services
├── .env                       # Variables d'environnement (ne pas commiter)
├── common/                    # Code partagé entre l'API et la webapp
│   ├── database_api.py        # Client pour communiquer avec l'API REST
│   └── openai_api.py          # Fonctions pour interagir avec OpenAI
│
├── database/                  # Service de base de données (SQLite)
│   ├── Dockerfile             # Dockerfile pour initialiser la DB
│   ├── init_db.py             # Script de création/initialisation de la DB
│   └── dnd_game.db            # (Optionnel : la base SQLite générée)
│
├── api/                       # Service API (FastAPI)
│   ├── Dockerfile             # Dockerfile pour l'API
│   ├── main.py                # Application FastAPI (modifiée pour importer depuis common)
│   └── requirements.txt       # Dépendances (fastapi, uvicorn, python-dotenv, openai, …)
│
└── webapp/                    # Interface utilisateur (Streamlit)
    ├── Dockerfile             # Dockerfile pour la webapp
    ├── app.py                 # Application Streamlit (modifiée pour importer depuis common)
    └── requirements.txt       # Dépendances (streamlit, requests, python-dotenv, openai, …)
