DndChatbotPoC/
├── app.py              (Streamlit principal avec Admin intégré)
├── database.py         (gestion SQLite synchronisée via Litestream)
├── openai_api.py       (gestion appels OpenAI)
├── requirements.txt    (incluant streamlit, openai, sqlite3)
├── Dockerfile          (facultatif : pour intégration Litestream facile sur Streamlit Cloud)
├── litestream.yml      (config Litestream pour synchronisation SQLite cloud)
└── .env                (variables d'environnement)