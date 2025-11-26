# 🚀 Améliorations et Refactoring Proposés

## 📋 Table des matières
1. [Architecture et Structure](#architecture-et-structure)
2. [Gestion d'erreurs et Logging](#gestion-derreurs-et-logging)
3. [Performance et Optimisation](#performance-et-optimisation)
4. [Sécurité](#sécurité)
5. [Qualité de code](#qualité-de-code)
6. [Configuration et Environnement](#configuration-et-environnement)
7. [Tests](#tests)
8. [Documentation](#documentation)

---

## 🏗️ Architecture et Structure

### Problèmes identifiés
- `main.py` trop volumineux (509 lignes) avec trop de responsabilités
- Pas de séparation claire entre les couches (API, Service, Repository)
- Logique métier mélangée avec la logique API

### Solutions proposées

#### 1. Restructuration en modules
```
api-job/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI uniquement
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── cv_analysis.py
│   │       └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cv_service.py    # Logique d'extraction CV
│   │   ├── job_service.py   # Logique de recherche/scoring
│   │   └── query_service.py # Génération de requêtes
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cv.py            # Modèles Pydantic pour CV
│   │   └── job.py           # Modèles Pydantic pour jobs
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # Configuration centralisée
│   └── utils/
│       ├── __init__.py
│       ├── llm_client.py    # Client LLM wrapper
│       ├── file_handler.py  # Gestion fichiers temporaires
│       └── template_loader.py # Chargement templates
├── tests/
│   ├── __init__.py
│   ├── test_cv_service.py
│   └── test_job_service.py
└── requirements.txt
```

#### 2. Utilisation de Pydantic pour la validation
```python
# app/models/cv.py
from pydantic import BaseModel, Field
from typing import List, Optional

class SkillSet(BaseModel):
    technical: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

class Experience(BaseModel):
    title: str
    company: str
    period: dict
    missions: List[str] = Field(default_factory=list)

class CVData(BaseModel):
    title: str
    address_city: str
    address_country: str = "France"
    summary: Optional[str] = None
    skills: SkillSet = Field(default_factory=SkillSet)
    experience: List[Experience] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
```

---

## 🔍 Gestion d'erreurs et Logging

### Problèmes identifiés
- Utilisation de `print()` au lieu d'un système de logging
- Gestion d'erreurs générique avec `except Exception`
- Pas de retry logic pour les appels API
- Pas de monitoring/observabilité

### Solutions proposées

#### 1. Système de logging structuré
```python
# app/utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(name: str, log_file: Path = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Format structuré
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optionnel)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

#### 2. Exceptions personnalisées
```python
# app/exceptions.py
class CVProcessingError(Exception):
    """Erreur lors du traitement du CV"""
    pass

class JobSearchError(Exception):
    """Erreur lors de la recherche d'offres"""
    pass

class LLMError(Exception):
    """Erreur lors de l'appel au LLM"""
    pass
```

#### 3. Retry logic avec exponential backoff
```python
# app/utils/retry.py
import time
from functools import wraps
from typing import Callable, TypeVar, Tuple

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (Exception,)
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée: {e}")
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator
```

---

## ⚡ Performance et Optimisation

### Problèmes identifiés
- Scoring séquentiel des offres (for loop)
- Pas de cache pour les requêtes répétées
- Pas de limite de taille de fichier
- Calcul de distance pour chaque offre (peut être coûteux)

### Solutions proposées

#### 1. Parallélisation du scoring
```python
# app/services/job_service.py
import asyncio
from typing import List

async def score_jobs_parallel(
    cv_data: dict,
    jobs: List[dict],
    max_workers: int = 5
) -> List[dict]:
    """Score plusieurs offres en parallèle"""
    semaphore = asyncio.Semaphore(max_workers)
    
    async def score_with_limit(job: dict) -> dict:
        async with semaphore:
            distance = await get_best_travel_time(job, cv_data)
            return await score_job_with_llm(cv_data, job, distance)
    
    tasks = [score_with_limit(job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filtrer les erreurs
    scored_jobs = [
        result for result in results 
        if isinstance(result, dict) and not isinstance(result, Exception)
    ]
    
    return scored_jobs
```

#### 2. Cache pour les requêtes LLM
```python
# app/utils/cache.py
from functools import lru_cache
import hashlib
import json

def cache_key(*args, **kwargs) -> str:
    """Génère une clé de cache à partir des arguments"""
    key_data = json.dumps(args, sort_keys=True) + json.dumps(kwargs, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()

# Utilisation avec Redis (optionnel)
from redis import Redis
redis_client = Redis(host='localhost', port=6379, db=0)

async def cached_llm_call(cache_key: str, llm_func: Callable):
    """Cache les appels LLM coûteux"""
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    result = await llm_func()
    redis_client.setex(cache_key, 3600, json.dumps(result))  # Cache 1h
    return result
```

#### 3. Validation de taille de fichier
```python
# app/api/endpoints/cv_analysis.py
from fastapi import UploadFile, File
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@app.post("/analyze-cv-and-match-jobs")
async def analyze_cv(file: UploadFile = File(...)):
    # Vérifier la taille
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux. Maximum: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    # ...
```

---

## 🔒 Sécurité

### Problèmes identifiés
- CORS ouvert à tous (`allow_origins=["*"]`)
- Pas de rate limiting
- Pas de validation stricte des fichiers uploadés
- Clés API exposées potentiellement dans les logs

### Solutions proposées

#### 1. Configuration CORS sécurisée
```python
# app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_credentials: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

#### 2. Rate Limiting
```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/analyze-cv-and-match-jobs")
@limiter.limit("5/minute")  # 5 requêtes par minute
async def analyze_cv(...):
    # ...
```

#### 3. Validation stricte des fichiers
```python
# app/utils/file_handler.py
from magic import Magic
import mimetypes

ALLOWED_MIME_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'image/png': ['.png'],
    'image/jpeg': ['.jpg', '.jpeg']
}

def validate_file(file: UploadFile) -> bool:
    """Valide le type MIME réel du fichier"""
    mime = Magic(mime=True)
    file_content = file.file.read()
    file.file.seek(0)
    
    detected_mime = mime.from_buffer(file_content)
    ext = Path(file.filename).suffix.lower()
    
    if detected_mime not in ALLOWED_MIME_TYPES:
        return False
    
    if ext not in ALLOWED_MIME_TYPES[detected_mime]:
        return False
    
    return True
```

---

## 📝 Qualité de code

### Problèmes identifiés
- Duplication de code (lecture de templates)
- Magic numbers et strings hardcodées
- Types hints incomplets
- Pas de docstrings complètes

### Solutions proposées

#### 1. Configuration centralisée
```python
# app/config/settings.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Keys
    groq_api_key: str
    job_scrapper_api_key: str
    google_maps_api_key: str
    
    # LLM Models
    cv_extraction_model: str = "openai/gpt-oss-20b"
    image_analysis_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    job_scoring_model: str = "openai/gpt-oss-120b"
    query_generation_model: str = "openai/gpt-oss-20b"
    
    # Limits
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_jobs_to_score: int = 50
    max_parallel_scoring: int = 5
    
    # Paths
    template_dir: Path = Path(__file__).parent.parent / "template_prompt"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### 2. Service de templates
```python
# app/utils/template_loader.py
from pathlib import Path
from functools import lru_cache

class TemplateLoader:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
    
    @lru_cache(maxsize=10)
    def load(self, filename: str) -> str:
        """Charge un template avec cache"""
        template_path = self.template_dir / filename
        if not template_path.exists():
            raise FileNotFoundError(f"Template {filename} introuvable")
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

template_loader = TemplateLoader(settings.template_dir)
```

---

## ⚙️ Configuration et Environnement

### Problèmes identifiés
- Variables d'environnement lues directement avec `os.getenv()`
- Pas de validation des configs
- Pas de gestion des environnements (dev/prod)

### Solutions proposées

#### 1. Utilisation de Pydantic Settings
```python
# app/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    # API Keys avec validation
    groq_api_key: str = Field(..., min_length=10)
    job_scrapper_api_key: str = Field(..., min_length=10)
    google_maps_api_key: str = Field(default="")
    
    # Environnement
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['development', 'staging', 'production']:
            raise ValueError('Environment must be development, staging or production')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

---

## 🧪 Tests

### Solutions proposées

#### 1. Structure de tests
```python
# tests/test_cv_service.py
import pytest
from app.services.cv_service import CVService
from app.models.cv import CVData

@pytest.fixture
def cv_service():
    return CVService()

@pytest.mark.asyncio
async def test_extract_cv_data(cv_service):
    # Test avec un CV mock
    cv_data = await cv_service.extract_from_file("test_cv.pdf")
    assert isinstance(cv_data, CVData)
    assert cv_data.address_city is not None

@pytest.mark.asyncio
async def test_generate_query(cv_service):
    cv_data = CVData(
        title="Data Scientist",
        address_city="Paris",
        address_country="France"
    )
    query = await cv_service.generate_search_query(cv_data)
    assert "data scientist" in query.lower()
    assert "paris" in query.lower()
```

#### 2. Tests d'intégration
```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

---

## 📚 Documentation

### Solutions proposées

#### 1. Documentation API avec OpenAPI/Swagger
- Déjà disponible avec FastAPI, mais peut être améliorée avec des exemples

#### 2. Documentation de code
```python
# Utiliser des docstrings détaillées
def score_job_with_llm(
    cv_data: CVData,
    job: dict,
    distance_minutes: int
) -> dict:
    """
    Score une offre d'emploi avec un LLM en fonction du CV.
    
    Args:
        cv_data: Données extraites du CV
        job: Dictionnaire contenant les informations de l'offre
        distance_minutes: Distance en minutes entre le candidat et l'offre
    
    Returns:
        Dictionnaire contenant l'offre avec son score de compatibilité
    
    Raises:
        LLMError: Si l'appel au LLM échoue
    """
    # ...
```

---

## 🎯 Priorités d'implémentation

### Phase 1 (Critique) - Semaine 1
1. ✅ Restructuration en modules (services, models)
2. ✅ Système de logging structuré
3. ✅ Configuration centralisée avec Pydantic
4. ✅ Gestion d'erreurs personnalisées

### Phase 2 (Important) - Semaine 2
5. ✅ Parallélisation du scoring
6. ✅ Validation de fichiers améliorée
7. ✅ Rate limiting
8. ✅ Tests unitaires de base

### Phase 3 (Amélioration) - Semaine 3
9. ✅ Cache pour les appels LLM
10. ✅ Retry logic avec backoff
11. ✅ Monitoring et métriques
12. ✅ Documentation complète

---

## 📊 Métriques à surveiller

- Temps de réponse moyen de l'API
- Taux d'erreur des appels LLM
- Nombre de requêtes par minute
- Taille moyenne des fichiers uploadés
- Taux de succès du matching

---

## 🔄 Migration progressive

Pour éviter de casser le code existant, proposer une migration progressive :

1. Créer la nouvelle structure à côté de l'ancienne
2. Migrer fonction par fonction
3. Garder l'ancien code en parallèle pendant la transition
4. Tests de régression à chaque étape

