# API Job Matching

API FastAPI pour analyser un CV, rechercher des offres d'emploi compatibles et les scorer selon leur pertinence.

## 🚀 Fonctionnalités

- **Extraction de données CV** : Analyse automatique de CV en format PDF, DOCX ou image (PNG, JPG, JPEG)
- **Recherche d'offres** : Scraping automatique d'offres d'emploi basé sur les mots-clés extraits du CV
- **Scoring intelligent** : Chaque offre est scorée par un LLM selon plusieurs critères :
  - Hard Skills (50%)
  - Expérience (25%)
  - Soft Skills (15%)
  - Formation (10%)
  - Distance géographique
  - Date de publication

## 📋 Prérequis

- Python 3.8+
- Clés API nécessaires (à configurer dans `.env`) :
  - `GROQ_API_KEY` : Clé API Groq pour les LLM
  - `JOB_SCRAPPER_API_KEY` : Clé API RapidAPI pour le scraping d'offres
  - `GOOGLE_MAPS_API_KEY` : Clé API Google Maps pour calculer les distances (optionnel)

## 🔧 Installation

1. Cloner le repository
```bash
git clone <repository-url>
cd api-job
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env et ajouter vos clés API
```

4. Lancer l'API
```bash
python main.py
# ou
uvicorn main:app --reload
```

L'API sera accessible sur `http://localhost:8000`

## 📖 Documentation API

### Endpoint principal : `/analyze-cv-and-match-jobs`

**Méthode** : `POST`

**Description** : Analyse un CV, recherche des offres d'emploi et les score selon leur compatibilité.

**Paramètres** :
- `file` (multipart/form-data) : Fichier CV (PDF, DOCX, PNG, JPG, JPEG)
- `num_pages` (query, optionnel) : Nombre de pages de résultats à scraper (défaut: 3)
- `max_jobs` (query, optionnel) : Nombre maximum d'offres à scorer (défaut: toutes)

**Réponse** :
```json
{
  "status": "ok",
  "cv_data": {
    "title": "Data Scientist",
    "address_city": "Paris",
    "address_country": "France",
    "summary": "...",
    "skills": {
      "technical": ["Python", "SQL", "Machine Learning"],
      "soft_skills": ["Communication", "Teamwork"],
      "languages": ["French", "English"]
    },
    "experience": [...],
    "education": [...],
    "certifications": [...],
    "keywords": [...]
  },
  "search_query": "Data Scientist Python SQL Machine Learning",
  "total_jobs_found": 50,
  "total_jobs_scored": 50,
  "scored_jobs": [
    {
      "job_id": "...",
      "job_title": "Data Scientist",
      "employer_name": "...",
      "job_description": "...",
      "job_city": "Paris",
      "job_country": "France",
      "job_apply_link": "...",
      "distance_between_cities": 15,
      "score": 85.5
    },
    ...
  ]
}
```

### Endpoint de santé : `/health`

**Méthode** : `GET`

**Description** : Vérifie que l'API fonctionne correctement.

**Réponse** :
```json
{
  "status": "ok",
  "message": "API Job Matching opérationnelle"
}
```

## 📝 Exemple d'utilisation

### Avec cURL
```bash
curl -X POST "http://localhost:8000/analyze-cv-and-match-jobs?num_pages=2&max_jobs=10" \
  -F "file=@/chemin/vers/votre/cv.pdf"
```

### Avec Python
```python
import requests

url = "http://localhost:8000/analyze-cv-and-match-jobs"
files = {"file": open("cv.pdf", "rb")}
params = {"num_pages": 2, "max_jobs": 10}

response = requests.post(url, files=files, params=params)
data = response.json()

print(f"Trouvé {data['total_jobs_scored']} offres")
for job in data['scored_jobs'][:5]:  # Top 5
    print(f"{job['job_title']} - Score: {job['score']}")
```

### Avec JavaScript/Fetch
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
  'http://localhost:8000/analyze-cv-and-match-jobs?num_pages=2&max_jobs=10',
  {
    method: 'POST',
    body: formData
  }
);

const data = await response.json();
console.log(data.scored_jobs);
```

## 🏗️ Architecture

Le système suit un workflow en plusieurs étapes :

1. **Upload du CV** → Fichier temporaire créé
2. **Extraction** → Analyse du CV avec LLM (Groq)
3. **Extraction de mots-clés** → Génération d'une requête de recherche
4. **Scraping** → Recherche d'offres via RapidAPI JSearch
5. **Calcul de distance** → Temps de trajet entre candidat et offre (Google Maps)
6. **Scoring** → Chaque offre est scorée par un LLM
7. **Tri et retour** → Offres triées par score décroissant

## 📁 Structure du projet

```
api-job/
├── main.py                 # API FastAPI principale
├── cv_reader.py            # Extraction de données CV
├── get_job_offers.py       # Scraping d'offres d'emploi
├── classifier_agent.py     # Agent de scoring (ancien, conservé pour compatibilité)
├── utils.py                # Utilitaires (calcul distances, etc.)
├── sheets_writer.py        # Écriture Google Sheets (optionnel)
├── template_prompt/       # Templates de prompts pour les LLM
│   ├── context.txt
│   ├── context_classifier.txt
│   ├── prompt_classifier.txt
│   ├── contexte_image.txt
│   └── prompt_image.txt
└── requirements.txt        # Dépendances Python
```

## 🔍 Format de données CV

Le CV extrait suit cette structure :

```json
{
  "title": "Titre du poste",
  "address_city": "Ville",
  "address_country": "Pays",
  "summary": "Résumé du profil",
  "skills": {
    "technical": ["Compétence 1", "Compétence 2"],
    "soft_skills": ["Soft skill 1"],
    "languages": ["Langue 1"]
  },
  "experience": [
    {
      "title": "Poste",
      "company": "Entreprise",
      "period": {"start": "YYYY-MM", "end": "YYYY-MM"},
      "missions": ["Mission 1", "Mission 2"]
    }
  ],
  "education": [...],
  "certifications": [...],
  "keywords": [...]
}
```

## ⚙️ Configuration

Les modèles LLM utilisés peuvent être modifiés dans `main.py` :
- CV extraction : `openai/gpt-oss-20b` (Groq)
- Image analysis : `meta-llama/llama-4-scout-17b-16e-instruct` (Groq)
- Job scoring : `openai/gpt-oss-120b` (Groq)

## 🐛 Dépannage

### Erreur "GROQ_API_KEY not found"
Vérifiez que votre fichier `.env` contient bien `GROQ_API_KEY=votre_cle`

### Erreur "Ville du candidat introuvable"
Le CV doit contenir une adresse ou ville clairement identifiable.

### Erreur "Aucune offre d'emploi trouvée"
Vérifiez votre clé `JOB_SCRAPPER_API_KEY` et que la recherche retourne des résultats.

## 📄 Licence

[À compléter]

## 👥 Auteurs

[À compléter]

