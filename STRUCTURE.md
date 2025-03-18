DndChatbotPoC/
├── docker-compose.yml           # orchestration Docker
├── database/                    # Base SQLite Dockerisée
│   ├── dnd_game.db              # ta base SQLite
│   ├── Dockerfile               # Dockerfile pour exécuter SQLite
│   ├── init_db.py               # Script de création et initialisation de la DB  ✅
│
├── api/                         # API intermédiaire (FastAPI)
│   ├── Dockerfile
│   ├── main.py                  # API REST claire
│   └── requirements.txt         # dépendances (FastAPI, uvicorn, SQLite, python-dotenv, openai)
│
├── webapp/
│   ├── Dockerfile
│   ├── app.py                   # app Streamlit avec UI admin et user
│   ├── openai_api.py
│   ├── database_api.py          # Client pour l'API REST
│   └── requirements.txt         # streamlit, requests, openai, python-dotenv
│
└── .env                         # secrets en local (non sur GitHub !)
