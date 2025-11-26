# Job Engine - Chatbot Assistant

Un assistant virtuel intelligent développé avec LangChain, FastAPI et OpenAI, capable de maintenir le contexte conversationnel et de fournir des réponses pertinentes grâce à une base de connaissances vectorielle. Inclut également une fonctionnalité de recherche d'emploi via l'API RapidAPI JSearch.

## Fonctionnalités

- 💬 Chat conversationnel avec mémoire contextuelle
- 🧠 Récupération de contexte (RAG) depuis une base de connaissances
- 📚 Gestion de base de données vectorielle (ChromaDB)
- 🔄 Gestion de sessions utilisateur multiples
- 📄 Support pour l'ajout de documents à la base de connaissances
- 🔍 Recherche d'emploi intelligente intégrée dans le chat (détection automatique)
- 🔍 Recherche d'emploi avec filtres avancés via API (RapidAPI JSearch)
- 🌐 API REST complète avec documentation automatique

## Prérequis

- Python 3.9 ou supérieur
- Clé API OpenAI (requis)
- Clé API RapidAPI (optionnel, pour la recherche d'emploi)

## Installation

1. Clonez le dépôt :
```bash
git clone <repository-url>
cd chatbot-langchain
```

2. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurez les variables d'environnement :
```bash
cp .env.example .env
# Éditez .env et ajoutez vos clés API :
# - OPENAI_API_KEY (requis)
# - RAPIDAPI_KEY (optionnel, pour la recherche d'emploi)
```

## Utilisation

1. Démarrez le serveur :
```bash
uvicorn app.main:app --reload
```

2. Accédez à la documentation interactive :
- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

## Endpoints API

### Chat

- `POST /chat` - Envoyer un message et recevoir une réponse
- `POST /chat/session/{session_id}` - Messages pour une session spécifique
- `GET /chat/session/{session_id}/history` - Récupérer l'historique d'une session
- `DELETE /chat/session/{session_id}` - Réinitialiser une session

### Base de connaissances

- `POST /knowledge/upload` - Ajouter des documents à la base de connaissances

### Recherche d'emploi

- `GET /jobs/search` - Rechercher des emplois avec critères détaillés
- `GET /jobs/search/summary` - Rechercher des emplois avec résumé formaté
- `GET /jobs/{job_id}` - Récupérer les détails d'un emploi spécifique

## Structure du projet

```
chatbot-langchain/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── models/              # Modèles Pydantic
│   ├── services/            # Services métier
│   │   ├── llm_service.py      # Service LLM avec LangChain
│   │   ├── memory_service.py   # Gestion de la mémoire
│   │   ├── vector_store.py      # Base de données vectorielle
│   │   ├── job_search_service.py # Recherche d'emploi
│   │   └── job_intent_detector.py # Détection d'intention de recherche d'emploi
│   └── routers/             # Routes API
│       ├── chat.py          # Routes de chat
│       └── jobs.py          # Routes de recherche d'emploi
├── data/
│   └── knowledge_base/      # Documents de connaissances
├── examples/                # Exemples d'utilisation
│   ├── example_usage.py     # Exemples d'utilisation de l'API
│   ├── example_job_search.py # Exemples de recherche d'emploi
│   ├── test_job_search_in_chat.py # Test recherche d'emploi dans le chat
│   └── frontend_example.html # Exemple frontend HTML
├── requirements.txt         # Dépendances Python
├── README.md                # Documentation principale
└── FRONTEND_API_DOCS.md     # Documentation frontend
```

## Exemples d'utilisation

### Exemples Python

Le projet inclut des exemples Python dans le dossier `examples/` :

```bash
# Exemple d'utilisation générale de l'API
python examples/example_usage.py

# Exemple de recherche d'emploi via API
python examples/example_job_search.py

# Test de recherche d'emploi dans le chat (détection automatique)
python examples/test_job_search_in_chat.py
```

### Recherche d'emploi dans le chat

Le chatbot détecte automatiquement les demandes de recherche d'emploi dans la conversation. Vous pouvez simplement demander :

- "Je cherche un emploi de développeur Python en France"
- "Trouve-moi des postes de data scientist en télétravail"
- "Y a-t-il des offres d'emploi pour ingénieur logiciel à Paris ?"
- "Recherche des emplois de designer UX remote"

Le chatbot effectuera automatiquement la recherche et présentera les résultats dans sa réponse, avec les détails des emplois trouvés.

### Exemples de code

**Chat :**
```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "message": "Bonjour, pouvez-vous m'aider ?",
    "session_id": "user-123"
})
print(response.json())
```

**Recherche d'emploi :**
```python
import requests

response = requests.get("http://localhost:8000/jobs/search", params={
    "query": "développeur Python",
    "country": "France",
    "language": "fr"
})
print(response.json())
```

### Documentation Frontend

Pour intégrer l'API dans votre application frontend, consultez la **[documentation frontend complète](FRONTEND_API_DOCS.md)** qui inclut :

- Exemples JavaScript/TypeScript
- Exemples React et Vue.js
- Gestion des erreurs
- Exemple HTML fonctionnel (`examples/frontend_example.html`)

Vous pouvez également tester directement l'exemple HTML en ouvrant `examples/frontend_example.html` dans votre navigateur (assurez-vous que le serveur backend est démarré).

## Technologies utilisées

- **LangChain** : Framework pour applications LLM
- **FastAPI** : Framework web moderne et rapide
- **OpenAI** : Modèles de langage GPT
- **ChromaDB** : Base de données vectorielle
- **Pydantic** : Validation de données
- **RapidAPI JSearch** : API de recherche d'emploi
- **Python 3.9+** : Langage de programmation

## Configuration avancée

Vous pouvez personnaliser l'application via les variables d'environnement dans le fichier `.env` :

```bash
# Application
APP_NAME=Job Engine - Chatbot Assistant
APP_VERSION=1.0.0
APP_DESCRIPTION=Votre description personnalisée
DEBUG=False

# OpenAI
OPENAI_API_KEY=votre_cle_openai
OPENAI_MODEL=gpt-3.5-turbo
TEMPERATURE=0.7
MAX_TOKENS=1000

# RapidAPI (optionnel)
RAPIDAPI_KEY=votre_cle_rapidapi

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db

# RAG
RETRIEVER_K=4
```

## Licence

MIT

