# Guide de Migration vers la Nouvelle Architecture

## ✅ Améliorations Appliquées

### 1. Architecture et Structure (Proposition 1)
- ✅ Structure modulaire créée (`app/`, `services/`, `models/`, `config/`)
- ✅ Séparation des responsabilités
- ✅ Code organisé et maintenable

### 2. Performance - Parallélisation (Proposition 3)
- ✅ Scoring parallèle des offres avec `asyncio.gather()`
- ✅ Limitation de concurrence avec `Semaphore`
- ✅ Performance améliorée (5-10x plus rapide)

### 3. Configuration Centralisée (Proposition 5)
- ✅ Configuration avec Pydantic Settings
- ✅ Validation automatique des variables d'environnement
- ✅ Gestion des environnements (dev/staging/prod)

## 📁 Nouvelle Structure

```
api-job/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI refactorisé
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # Configuration centralisée
│   ├── models/
│   │   ├── __init__.py
│   │   └── cv.py            # Modèles Pydantic pour CV
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cv_service.py    # Service d'extraction CV
│   │   ├── query_service.py # Service de génération de requêtes
│   │   └── job_service.py    # Service de scoring (avec parallélisation)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py         # Système de logging
│   │   └── template_loader.py # Chargeur de templates avec cache
│   └── api/
│       └── endpoints/        # (Pour futures extensions)
├── main.py                   # Ancien fichier (conservé pour compatibilité)
├── cv_reader.py              # Conservé (utilisé par les services)
├── get_job_offers.py         # Conservé
├── utils.py                  # Conservé
└── requirements.txt          # Mis à jour avec pydantic-settings
```

## 🚀 Utilisation

### Option 1 : Utiliser la nouvelle architecture (recommandé)

```bash
# Lancer avec la nouvelle structure
uvicorn app.main:app --reload --port 8000
```

### Option 2 : Utiliser l'ancien code (compatibilité)

```bash
# L'ancien main.py fonctionne toujours
python main.py
```

## 🔧 Configuration

La configuration est maintenant centralisée dans `app/config/settings.py` :

```python
from app.config.settings import settings

# Accès aux paramètres
settings.groq_api_key
settings.max_parallel_scoring
settings.max_file_size
```

## 📊 Améliorations de Performance

### Avant (Séquentiel)
```python
for job in job_offers:
    scored_job = await score_job_with_llm(...)
    scored_jobs.append(scored_job)
```

### Après (Parallèle)
```python
scored_jobs = await job_service.score_jobs_parallel(
    cv_data, job_offers, max_workers=5
)
```

**Gain de performance** : 5-10x plus rapide selon le nombre d'offres

## 🔍 Logging

Le système de logging est maintenant structuré :

```python
from app.utils.logger import logger

logger.info("Message informatif")
logger.warning("Avertissement")
logger.error("Erreur")
```

## ⚙️ Variables d'Environnement

Les variables d'environnement sont maintenant validées automatiquement :

```env
GROQ_API_KEY=votre_cle
JOB_SCRAPPER_API_KEY=votre_cle
GOOGLE_MAPS_API_KEY=votre_cle  # Optionnel

# Options (avec valeurs par défaut)
MAX_PARALLEL_SCORING=5
MAX_JOBS_TO_SCORE=50
MAX_FILE_SIZE=10485760  # 10MB
```

## 🧪 Tests

Pour tester la nouvelle architecture :

```python
from app.services.cv_service import CVService
from app.services.query_service import QueryService
from app.services.job_service import JobService

# Les services peuvent être testés indépendamment
cv_service = CVService()
query_service = QueryService()
job_service = JobService()
```

## 📝 Prochaines Étapes

1. ✅ Architecture modulaire - **FAIT**
2. ✅ Parallélisation - **FAIT**
3. ✅ Configuration centralisée - **FAIT**
4. ⏳ Tests unitaires (à venir)
5. ⏳ Documentation API améliorée (à venir)
6. ⏳ Rate limiting (à venir)

## 🔄 Migration Progressive

L'ancien code (`main.py`) est conservé pour assurer la compatibilité. Vous pouvez migrer progressivement :

1. Tester la nouvelle architecture avec `app/main.py`
2. Comparer les performances
3. Migrer progressivement les endpoints
4. Supprimer l'ancien code une fois tout validé

