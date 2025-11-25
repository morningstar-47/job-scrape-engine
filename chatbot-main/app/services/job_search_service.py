"""
Service de recherche d'emploi avec RapidAPI JSearch
"""
import requests
from typing import Dict, Optional, Any
from app.config import settings


class JobSearchService:
    """Service pour rechercher des emplois via l'API JSearch de RapidAPI"""
    
    def __init__(self):
        """Initialise le service avec la clé API"""
        self.api_key = settings.rapidapi_key
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
    
    def search_jobs(
        self,
        query: str,
        country: Optional[str] = None,
        language: Optional[str] = None,
        num_pages: int = 1,
        employment_types: Optional[str] = None,
        job_requirements: Optional[str] = None,
        date_posted: Optional[str] = None,
        remote_jobs_only: bool = False
    ) -> Dict[str, Any]:
        """
        Recherche des emplois selon les critères spécifiés
        
        Args:
            query: Termes de recherche (titre du poste, compétences, etc.)
            country: Code pays ISO à 2 lettres (fr, de, es, it, be, ch, ca, us, etc.)
            language: Langue (fr, en, es, etc.)
            num_pages: Nombre de pages à récupérer (défaut: 1)
            employment_types: Types d'emploi (FULLTIME, PARTTIME, CONTRACTOR, INTERN)
            job_requirements: Exigences (under_3_years_experience, more_than_3_years_experience, no_experience, no_degree)
            date_posted: Date de publication (today, 3days, week, month)
            remote_jobs_only: Rechercher uniquement les emplois à distance
            
        Returns:
            Dictionnaire contenant les résultats de la recherche
        """
        if not self.api_key:
            return {
                "error": "Clé API RapidAPI non configurée",
                "jobs": [],
                "total": 0
            }
        
        try:
            # Construire les paramètres de la requête
            params = {
                "query": query,
                "language": language,
                "num_pages": str(num_pages)
            }
            
            if country:
                params["country"] = country
            
            if employment_types:
                params["employment_types"] = employment_types
            
            if job_requirements:
                params["job_requirements"] = job_requirements
            
            if date_posted:
                params["date_posted"] = date_posted
            
            params["remote_jobs_only"] = "true" if remote_jobs_only else "false"
            
            # Faire l'appel à l'API
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Formater les résultats
            jobs = data.get("data", [])
            
            return {
                "jobs": jobs,
                "total": len(jobs),
                "query": query,
                "country": country,
                "language": language,
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Erreur lors de la recherche d'emploi: {str(e)}",
                "jobs": [],
                "total": 0
            }
        except Exception as e:
            return {
                "error": f"Erreur inattendue: {str(e)}",
                "jobs": [],
                "total": 0
            }
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un emploi spécifique
        
        Args:
            job_id: Identifiant de l'emploi
            
        Returns:
            Dictionnaire contenant les détails de l'emploi
        """
        if not self.api_key:
            return {"error": "Clé API RapidAPI non configurée"}
        
        try:
            response = requests.get(
                f"{self.base_url}/job-details",
                headers=self.headers,
                params={"job_id": job_id},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("data", {})
        
        except requests.exceptions.RequestException as e:
            return {"error": f"Erreur lors de la récupération des détails: {str(e)}"}
        except Exception as e:
            return {"error": f"Erreur inattendue: {str(e)}"}
    
    def format_job_summary(self, job: Dict[str, Any]) -> str:
        """
        Formate un emploi en résumé texte lisible
        
        Args:
            job: Dictionnaire contenant les informations de l'emploi
            
        Returns:
            Chaîne formatée avec les informations de l'emploi
        """
        title = job.get("job_title", "Titre non spécifié")
        company = job.get("employer_name", "Entreprise non spécifiée")
        location = job.get("job_city", "")
        if job.get("job_state"):
            location += f", {job.get('job_state')}"
        if job.get("job_country"):
            location += f", {job.get('job_country')}"
        
        job_type = job.get("job_employment_type", "")
        is_remote = job.get("job_is_remote", False)
        remote_text = " (Télétravail)" if is_remote else ""
        
        posted = job.get("job_posted_at_datetime_utc", "")
        
        summary = f"**{title}** chez {company}"
        if location:
            summary += f" - {location}"
        if job_type:
            summary += f" ({job_type}{remote_text})"
        if posted:
            summary += f"\nPublié le: {posted}"
        
        return summary


# Instance globale du service
job_search_service = JobSearchService()

