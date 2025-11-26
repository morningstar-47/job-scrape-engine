"""Point d'entrée principal de l'API FastAPI"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
import asyncio
import json
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.utils.logger import logger
from app.services.cv_service import CVService
from app.services.query_service import QueryService
from app.services.job_service import JobService
from get_job_offers import search_jobs

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Job Matching API",
    description="API pour analyser un CV, scraper les offres d'emploi et les scorer selon la compatibilité",
    version="3.0.0",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des services
cv_service = CVService()
query_service = QueryService()
job_service = JobService()


def _write_temp_file(content: bytes, suffix: str) -> str:
    """Écrit un fichier temporaire et retourne son chemin"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return tmp.name


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
    3. Utilise un LLM pour générer une requête de recherche optimale
    4. Scrape les offres d'emploi avec cette requête
    5. Score chaque offre avec un LLM (en parallèle)
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
        
        # 2. Vérifier la taille du fichier
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Maximum: {settings.max_file_size / 1024 / 1024}MB"
            )
        
        # 3. Sauvegarder temporairement le fichier
        tmp_path = _write_temp_file(content, suffix=ext)
        
        try:
            # 4. Extraire les données du CV avec le service
            logger.info(f"Extraction du CV: {file.filename}")
            cv_data = await cv_service.extract_from_file(Path(tmp_path), ext)
            
            # 5. Vérifier que la ville est présente
            if not cv_data.address_city:
                raise HTTPException(
                    status_code=400,
                    detail="Impossible d'extraire la ville du candidat du CV"
                )
            
            # 6. Générer la requête de recherche avec le service
            logger.info("Génération de la requête de recherche")
            search_query = await query_service.generate_search_query(cv_data)
            
            # 7. Scraper les offres d'emploi
            logger.info(f"Recherche d'offres avec la requête: {search_query}")
            try:
                jobs_result = await asyncio.to_thread(
                    search_jobs,
                    search_query,
                    cv_data.address_city,
                    num_pages=num_pages,
                    country=cv_data.address_country.lower() if cv_data.address_country else "fr",
                    language="fr",
                    remote_jobs_only=False
                )
                
                jobs_data = json.loads(jobs_result)
                job_offers = jobs_data.get("data", [])
                
                if not job_offers:
                    logger.warning(f"Aucune offre trouvée pour la requête: {search_query}")
                    return JSONResponse(content={
                        "status": "ok",
                        "message": f"Aucune offre d'emploi trouvée pour la requête: {search_query}",
                        "cv_data": cv_data.model_dump(),
                        "search_query": search_query,
                        "scored_jobs": []
                    })
                    
            except Exception as e:
                logger.error(f"Erreur lors du scraping: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de la recherche d'offres d'emploi: {str(e)}"
                )
            
            # 8. Limiter le nombre d'offres si demandé
            if max_jobs:
                job_offers = job_offers[:max_jobs]
            elif len(job_offers) > settings.max_jobs_to_score:
                job_offers = job_offers[:settings.max_jobs_to_score]
                logger.info(f"Limitation à {settings.max_jobs_to_score} offres")
            
            # 9. Scorer les offres EN PARALLÈLE avec le service
            logger.info(f"Scoring de {len(job_offers)} offres en parallèle")
            scored_jobs = await job_service.score_jobs_parallel(
                cv_data,
                job_offers,
                max_workers=settings.max_parallel_scoring
            )
            
            # 10. Retourner les résultats
            logger.info(f"Traitement terminé: {len(scored_jobs)} offres scorées")
            return JSONResponse(content={
                "status": "ok",
                "cv_data": cv_data.model_dump(),
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
        logger.error(f"Erreur lors du traitement: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    return JSONResponse(content={
        "status": "ok",
        "message": "API Job Matching opérationnelle",
        "version": "3.0.0"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

