from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
import asyncio
import json
from pathlib import Path
from cv_reader import read_cv, ask_vision
from get_job_offers import search_jobs
from utils import travel_time_from_cities, select_from_job
from groq import Groq
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(
    title="Job Matching API",
    description="API pour analyser un CV, scraper les offres d'emploi et les scorer selon la compatibilité",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du client Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _write_temp_file(content: bytes, suffix: str) -> str:
    """Écrit un fichier temporaire et retourne son chemin"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return tmp.name


def read_template_file(filename: str) -> str:
    """Lit un fichier template depuis le dossier template_prompt"""
    template_path = Path(__file__).parent / "template_prompt" / filename
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


async def generate_search_query_with_llm(cv_data: dict) -> str:
    """
    Utilise un LLM pour analyser le CV et générer une requête de recherche optimale.
    Exemple: "data scientist à Paris"
    """
    try:
        # Lire le template de prompt
        prompt_template = read_template_file("prompt_query_generator.txt")
        
        # Construire le prompt avec les données du CV pour déterminer le poste souhaité
        # Inclure plus d'informations pour que le LLM puisse mieux déterminer le poste souhaité
        experiences = cv_data.get("experience", [])
        main_experiences = experiences[:3] if experiences else []  # 3 expériences les plus récentes
        
        cv_summary = {
            "titre_cv": cv_data.get("title", ""),
            "ville": cv_data.get("address_city", ""),
            "pays": cv_data.get("address_country", ""),
            "resume": cv_data.get("summary", "")[:300] if cv_data.get("summary") else "",  # Résumé complet
            "competences_techniques": cv_data.get("skills", {}).get("technical", [])[:8] if isinstance(cv_data.get("skills"), dict) else [],
            "experiences_professionnelles": [
                {
                    "poste": exp.get("title", ""),
                    "entreprise": exp.get("company", ""),
                    "periode": f"{exp.get('period', {}).get('start', '')} - {exp.get('period', {}).get('end', '')}",
                    "missions": exp.get("missions", [])[:3]  # 3 missions principales
                }
                for exp in main_experiences
            ],
            "mots_cles": cv_data.get("keywords", [])[:5] if cv_data.get("keywords") else []
        }
        
        user_prompt = (
            prompt_template + "\n" +
            json.dumps(cv_summary, ensure_ascii=False, indent=2)
        )
        
        # Appel au LLM pour générer la requête
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un expert en recrutement et en analyse de CV. Ton rôle est d'analyser en profondeur un CV pour déterminer le POSTE SOUHAITÉ du candidat en te basant sur ses expériences, compétences et objectifs professionnels, puis de générer une requête de recherche d'emploi optimale et précise."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="openai/gpt-oss-20b",
            temperature=0.3,
            max_tokens=50
        )
        
        query = response.choices[0].message.content.strip()
        
        # Nettoyer la requête (enlever les guillemets si présents)
        query = query.strip('"').strip("'").strip()
        
        # Vérifier que la requête est valide et pas trop longue
        # Elle doit contenir au maximum 5 mots (poste + "à" + ville)
        words = query.split()
        
        # Log pour déboguer
        print(f"🎯 Poste souhaité déterminé par le LLM: {query}")
        print(f"📝 Titre CV original: {cv_data.get('title', 'N/A')}")
        print(f"📊 Nombre de mots dans la requête: {len(words)}")
        
        # Fallback si la requête est vide, trop courte ou trop longue
        if not query or len(query) < 3:
            print("⚠️ Requête LLM vide ou trop courte, utilisation du fallback")
            return extract_keywords_fallback(cv_data)
        
        # Si la requête est trop longue (plus de 6 mots), utiliser le fallback
        if len(words) > 6:
            print(f"⚠️ Requête LLM trop longue ({len(words)} mots), utilisation du fallback")
            return extract_keywords_fallback(cv_data)
        
        return query
        
    except Exception as e:
        print(f"Erreur lors de la génération de la requête avec LLM: {e}")
        # Fallback vers la méthode simple
        return extract_keywords_fallback(cv_data)


def extract_keywords_fallback(cv_data: dict) -> str:
    """
    Méthode de fallback pour extraire UNIQUEMENT le poste souhaité du CV si le LLM échoue.
    Retourne uniquement le nom du poste/métier, sans ville ni mots-clés supplémentaires.
    """
    # 1. Essayer d'extraire le poste des expériences professionnelles (le plus fiable)
    experiences = cv_data.get("experience", [])
    if experiences and len(experiences) > 0:
        # Prendre le poste de la première expérience (la plus récente)
        job_title = experiences[0].get("title", "")
        if job_title and len(job_title.strip()) > 2:
            # Nettoyer et simplifier le titre du poste
            job_title_clean = job_title.strip()
            # Limiter à 2-3 mots maximum
            words = job_title_clean.split()
            if len(words) > 3:
                job_title_clean = " ".join(words[:3])
            return job_title_clean.lower()
    
    # 2. Si pas d'expérience, analyser le titre du CV
    title = cv_data.get("title", "")
    if title:
        title_lower = title.lower()
        
        # Enlever les mentions d'études
        title_clean = title_lower
        title_clean = title_clean.replace("étudiant", "").replace("étudiante", "")
        title_clean = title_clean.replace("en mastère", "").replace("en master", "")
        title_clean = title_clean.replace("en licence", "").replace("en bachelor", "")
        title_clean = title_clean.replace("diplômé", "").replace("diplômée", "")
        title_clean = title_clean.strip()
        
        # Mapper les domaines d'études vers des métiers réels (noms simples)
        domain_mapping = {
            "finance d'entreprise": "comptabilité",
            "finance": "comptabilité",
            "comptabilité": "comptabilité",
            "gestion": "comptabilité",
            "contrôle de gestion": "comptabilité",
            "marketing": "marketing",
            "communication": "communication",
            "informatique": "développement",
            "développement": "développement",
            "programmation": "développement",
            "data": "data analyst",
            "scientist": "data scientist",
            "ressources humaines": "rh",
            "rh": "rh",
            "commerce": "commerce",
            "vente": "commerce",
            "juridique": "juridique",
            "droit": "juridique",
            "ingénieur": "ingénieur",
            "design": "design",
            "graphisme": "design"
        }
        
        # Chercher un mapping dans le titre (vérifier d'abord les correspondances exactes)
        for domain, job in domain_mapping.items():
            if domain in title_clean:
                print(f"[Mapping] '{domain}' -> '{job}'")
                return job
        
        # Si pas de mapping, extraire les mots-clés du domaine
        if title_clean:
            words = title_clean.split()
            # Prendre les 1-2 premiers mots significatifs
            if len(words) >= 2:
                # Prendre les 2 premiers mots qui représentent le domaine
                domain = " ".join(words[:2])
                return domain
            elif len(words) == 1:
                return words[0]
    
    # 3. Essayer avec les compétences techniques principales
    skills = cv_data.get("skills", {})
    if isinstance(skills, dict) and skills.get("technical"):
        tech_skills = skills["technical"]
        if tech_skills and len(tech_skills) > 0:
            # Prendre la première compétence technique principale
            main_skill = tech_skills[0].lower()
            return main_skill
    
    # 4. Fallback final
    return "emploi"


async def score_job_with_llm(
    cv_data: dict,
    job: dict,
    distance_minutes: int
) -> dict:
    """
    Score une offre d'emploi avec un LLM en fonction du CV.
    """
    try:
        # Lire les templates
        context = read_template_file("context_classifier.txt")
        user_prompt_template = read_template_file("prompt_classifier.txt")
        
        # Préparer les données pour le prompt
        job_filtered = select_from_job(job)
        
        # Construire le prompt utilisateur
        user_prompt = (
            user_prompt_template + "\n\n" +
            "CV du candidat:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2) + "\n\n" +
            "Offre d'emploi:\n" + json.dumps(job_filtered, ensure_ascii=False, indent=2) + "\n\n" +
            "Distance en minutes: " + str(distance_minutes)
        )
        
        # Appel au LLM
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": user_prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        scored_job = json.loads(response.choices[0].message.content)
        
        # S'assurer que tous les champs de l'offre sont présents
        scored_job.update(job_filtered)
        scored_job["distance_between_cities"] = distance_minutes
        
        return scored_job
        
    except Exception as e:
        print(f"Erreur lors du scoring de l'offre {job.get('job_id', 'unknown')}: {e}")
        # Retourner l'offre avec un score de 0 en cas d'erreur
        job_filtered = select_from_job(job)
        job_filtered["score"] = 0
        job_filtered["distance_between_cities"] = distance_minutes
        return job_filtered


async def get_best_travel_time(
    job: dict,
    cv_data: dict
) -> int:
    """
    Calcule le meilleur temps de trajet entre la ville du candidat et celle de l'offre.
    """
    try:
        origin_city = job.get("job_city", "")
        origin_country = job.get("job_country", "France")
        dest_city = cv_data.get("address_city", "")
        dest_country = cv_data.get("address_country", "France")
        
        if not origin_city or not dest_city:
            return 1000  # Distance par défaut élevée
        
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("⚠️ GOOGLE_MAPS_API_KEY non configurée, utilisation d'une distance par défaut")
            return 1000
        
        time_by_transport_mean = []
        for transport_mean in ["WALK", "DRIVE", "TRANSIT", "BICYCLE"]:
            try:
                minutes = travel_time_from_cities(
                    api_key=api_key,
                    origin_city=origin_city,
                    origin_country=origin_country,
                    destination_city=dest_city,
                    destination_country=dest_country,
                    travel_mode=transport_mean
                )
                time_by_transport_mean.append(minutes)
            except Exception as e:
                print(f"Erreur calcul trajet ({transport_mean}): {e}")
                continue
        
        return min(time_by_transport_mean) if time_by_transport_mean else 1000
        
    except Exception as e:
        print(f"Erreur lors du calcul du temps de trajet: {e}")
        return 1000


@app.post("/analyze-cv-and-match-jobs")
async def analyze_cv_and_match_jobs(
    file: UploadFile = File(...),
    num_pages: int = 3,
    max_jobs: Optional[int] = None
):
    """
    Endpoint principal qui :
    1. Reçoit un CV (PDF, DOCX ou image)
    2. Extrait les données en JSON
    3. Utilise un LLM pour générer une requête de recherche optimale (ex: "data scientist à Paris")
    4. Scrape les offres d'emploi avec cette requête
    5. Score chaque offre avec un LLM
    6. Retourne les offres triées par score
    """
    try:
        # 1. Vérifier le format du fichier
        ext = Path(file.filename).suffix.lower()
        if ext not in [".pdf", ".docx", ".png", ".jpg", ".jpeg"]:
            raise HTTPException(
                status_code=400,
                detail="Format non supporté. Formats acceptés: PDF, DOCX, PNG, JPG, JPEG"
            )
        
        # 2. Sauvegarder temporairement le fichier
        content = await file.read()
        tmp_path = _write_temp_file(content, suffix=ext)
        
        try:
            # 3. Extraire les données du CV
            if ext in [".pdf", ".docx"]:
                cv_result = await asyncio.to_thread(read_cv, tmp_path)
                cv_data = json.loads(cv_result)
            elif ext in [".png", ".jpg", ".jpeg"]:
                cv_result = await asyncio.to_thread(ask_vision, tmp_path)
                cv_data = cv_result
            else:
                raise HTTPException(status_code=400, detail="Format non supporté")
            
            # Normaliser les données (gérer les différents formats de sortie)
            # Format image (prompt_image.txt)
            if "ville_candidat" in cv_data:
                cv_data["address_city"] = cv_data.pop("ville_candidat")
            if "type_poste" in cv_data:
                cv_data["title"] = cv_data.pop("type_poste")
            if "description_candidat" in cv_data and not cv_data.get("summary"):
                cv_data["summary"] = cv_data.pop("description_candidat")
            if "competences" in cv_data and not cv_data.get("skills"):
                # Convertir le format simple en format structuré
                competences = cv_data.pop("competences", [])
                cv_data["skills"] = {
                    "technical": competences if isinstance(competences, list) else [],
                    "soft_skills": [],
                    "languages": []
                }
            
            # Vérifier que les données essentielles sont présentes
            if not cv_data.get("address_city"):
                raise HTTPException(
                    status_code=400,
                    detail="Impossible d'extraire la ville du candidat du CV"
                )
            
            # S'assurer que les champs essentiels existent
            if not cv_data.get("title"):
                cv_data["title"] = "Developer"  # Valeur par défaut
            if not cv_data.get("address_country"):
                cv_data["address_country"] = "France"  # Valeur par défaut
            if not cv_data.get("skills"):
                cv_data["skills"] = {
                    "technical": [],
                    "soft_skills": [],
                    "languages": []
                }
            if not cv_data.get("keywords"):
                cv_data["keywords"] = []
            
            # 4. Générer la requête de recherche avec un LLM
            search_query = await generate_search_query_with_llm(cv_data)
            
            city = cv_data.get("address_city", "")
            country = cv_data.get("address_country", "France")
            
            if not city:
                raise HTTPException(
                    status_code=400,
                    detail="Ville du candidat introuvable dans le CV"
                )
            
            # 5. Scraper les offres d'emploi
            try:
                jobs_result = await asyncio.to_thread(
                    search_jobs,
                    search_query,
                    city,
                    num_pages=num_pages,
                    country=country.lower() if country else "fr",
                    language="fr",  # Langue française par défaut
                    remote_jobs_only=False  # Inclure toutes les offres (présentiel + remote)
                )
                
                jobs_data = json.loads(jobs_result)
                job_offers = jobs_data.get("data", [])
                
                if not job_offers:
                    print(f"⚠️ Aucune offre trouvée pour la requête: {search_query}")
                    return JSONResponse(content={
                        "status": "ok",
                        "message": f"Aucune offre d'emploi trouvée pour la requête: {search_query}",
                        "cv_data": cv_data,
                        "search_query": search_query,
                        "scored_jobs": []
                    })
                    
            except Exception as e:
                print(f"❌ Erreur lors du scraping: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de la recherche d'offres d'emploi: {str(e)}"
                )
            
            if not job_offers:
                return JSONResponse(content={
                    "status": "ok",
                    "message": "Aucune offre d'emploi trouvée",
                    "cv_data": cv_data,
                    "scored_jobs": []
                })
            
            # Limiter le nombre d'offres si demandé
            if max_jobs:
                job_offers = job_offers[:max_jobs]
            
            # 6. Scorer chaque offre avec le LLM
            scored_jobs = []
            for job in job_offers:
                try:
                    # Calculer la distance
                    distance = await get_best_travel_time(job, cv_data)
                    
                    # Scorer avec le LLM
                    scored_job = await score_job_with_llm(cv_data, job, distance)
                    scored_jobs.append(scored_job)
                    
                except Exception as e:
                    print(f"Erreur lors du traitement de l'offre {job.get('job_id')}: {e}")
                    continue
            
            # 7. Trier par score décroissant
            scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # 8. Retourner les résultats
            return JSONResponse(content={
                "status": "ok",
                "cv_data": cv_data,
                "search_query": search_query,
                "total_jobs_found": len(job_offers),
                "total_jobs_scored": len(scored_jobs),
                "scored_jobs": scored_jobs
            })
            
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.remove(tmp_path)
            except Exception:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    return JSONResponse(content={
        "status": "ok",
        "message": "API Job Matching opérationnelle"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
