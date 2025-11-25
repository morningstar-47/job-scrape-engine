"""
Routes API pour la recherche d'emploi
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.job_search_service import job_search_service


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/search")
async def search_jobs(
    query: str = Query(..., description="Termes de recherche (titre du poste, compétences, etc.)"),
    country: Optional[str] = Query(None, description="Code pays ISO à 2 lettres (fr, de, es, it, be, ch, ca, us, etc.)"),
    language: Optional[str] = Query("fr", description="Langue optionnelle"),
    num_pages: int = Query(1, ge=1, le=10, description="Nombre de pages à récupérer"),
    employment_types: Optional[str] = Query(
        None,
        description="Types d'emploi: FULLTIME, PARTTIME, CONTRACTOR, INTERN"
    ),
    job_requirements: Optional[str] = Query(
        None,
        description="Exigences: under_3_years_experience, more_than_3_years_experience, no_experience, no_degree"
    ),
    date_posted: Optional[str] = Query(
        None,
        description="Date de publication: today, 3days, week, month"
    ),
    remote_jobs_only: bool = Query(False, description="Rechercher uniquement les emplois à distance")
):
    """
    Recherche des emplois selon les critères spécifiés
    
    - **query**: Termes de recherche (requis)
    - **country**: Code pays ISO à 2 lettres (fr, de, es, it, be, ch, ca, us, etc.)
    - **language**: Langue optionnelle
    - **num_pages**: Nombre de pages (défaut: 1, max: 10)
    - **employment_types**: Types d'emploi
    - **job_requirements**: Exigences
    - **date_posted**: Date de publication
    - **remote_jobs_only**: Emplois à distance uniquement
    """
    try:
        result = job_search_service.search_jobs(
            query=query,
            country=country,
            language=language,
            num_pages=num_pages,
            employment_types=employment_types,
            job_requirements=job_requirements,
            date_posted=date_posted,
            remote_jobs_only=remote_jobs_only
        )
        
        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche d'emploi: {str(e)}"
        )


@router.get("/{job_id}")
async def get_job_details(job_id: str):
    """
    Récupère les détails d'un emploi spécifique
    
    - **job_id**: Identifiant de l'emploi
    """
    try:
        result = job_search_service.get_job_details(job_id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des détails: {str(e)}"
        )


@router.get("/search/summary")
async def search_jobs_summary(
    query: str = Query(..., description="Termes de recherche"),
    country: Optional[str] = Query(None, description="Pays"),
    language: Optional[str] = Query("fr", description="Langue optionnelle"),
    limit: int = Query(5, ge=1, le=20, description="Nombre maximum de résultats")
):
    """
    Recherche des emplois et retourne un résumé formaté
    
    - **query**: Termes de recherche
    - **country**: Pays optionnel
    - **limit**: Nombre maximum de résultats (défaut: 5, max: 20)
    """
    try:
        result = job_search_service.search_jobs(
            query=query,
            country=country,
            language=language,
        )
        
        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        jobs = result.get("jobs", [])[:limit]
        
        summaries = []
        for job in jobs:
            summary = job_search_service.format_job_summary(job)
            summaries.append({
                "summary": summary,
                "job_id": job.get("job_id"),
                "job_apply_link": job.get("job_apply_link")
            })
        
        return {
            "query": query,
            "country": country,
            "total_found": result.get("total", 0),
            "results": summaries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche: {str(e)}"
        )

