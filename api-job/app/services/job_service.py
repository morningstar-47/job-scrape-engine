"""Service pour le scoring et le matching des offres d'emploi"""
import json
import asyncio
from typing import List, Dict

from app.models.cv import CVData
from app.config.settings import settings
from app.utils.template_loader import template_loader
from app.utils.logger import logger
from groq import Groq
from utils import travel_time_from_cities, select_from_job


class JobService:
    """Service pour scorer et matcher les offres d'emploi"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.logger = logger
    
    async def score_job(
        self,
        cv_data: CVData,
        job: Dict,
        distance_minutes: int
    ) -> Dict:
        """
        Score une offre d'emploi avec un LLM
        
        Args:
            cv_data: Données du CV
            job: Dictionnaire contenant l'offre d'emploi
            distance_minutes: Distance en minutes entre le candidat et l'offre
            
        Returns:
            Dictionnaire contenant l'offre avec son score
        """
        try:
            context = template_loader.load("context_classifier.txt")
            user_prompt_template = template_loader.load("prompt_classifier.txt")
            
            job_filtered = select_from_job(job)
            
            # Convertir CVData en dict pour le prompt
            cv_dict = cv_data.model_dump()
            
            user_prompt = (
                user_prompt_template + "\n\n" +
                "CV du candidat:\n" + json.dumps(cv_dict, ensure_ascii=False, indent=2) + "\n\n" +
                "Offre d'emploi:\n" + json.dumps(job_filtered, ensure_ascii=False, indent=2) + "\n\n" +
                "Distance en minutes: " + str(distance_minutes)
            )
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_prompt}
                ],
                model=settings.job_scoring_model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            scored_job = json.loads(response.choices[0].message.content)
            scored_job.update(job_filtered)
            scored_job["distance_between_cities"] = distance_minutes
            
            return scored_job
            
        except Exception as e:
            self.logger.error(f"Erreur lors du scoring de l'offre {job.get('job_id', 'unknown')}: {e}")
            # Retourner l'offre avec un score de 0 en cas d'erreur
            job_filtered = select_from_job(job)
            job_filtered["score"] = 0
            job_filtered["distance_between_cities"] = distance_minutes
            return job_filtered
    
    async def get_best_travel_time(
        self,
        job: Dict,
        cv_data: CVData
    ) -> int:
        """
        Calcule le meilleur temps de trajet entre la ville du candidat et celle de l'offre
        
        Args:
            job: Dictionnaire contenant l'offre d'emploi
            cv_data: Données du CV
            
        Returns:
            Temps de trajet en minutes
        """
        try:
            origin_city = job.get("job_city", "")
            origin_country = job.get("job_country", "France")
            dest_city = cv_data.address_city
            dest_country = cv_data.address_country
            
            if not origin_city or not dest_city:
                return 1000  # Distance par défaut élevée
            
            if not settings.google_maps_api_key:
                self.logger.warning("GOOGLE_MAPS_API_KEY non configurée, utilisation d'une distance par défaut")
                return 1000
            
            time_by_transport_mean = []
            for transport_mean in ["WALK", "DRIVE", "TRANSIT", "BICYCLE"]:
                try:
                    minutes = travel_time_from_cities(
                        api_key=settings.google_maps_api_key,
                        origin_city=origin_city,
                        origin_country=origin_country,
                        destination_city=dest_city,
                        destination_country=dest_country,
                        travel_mode=transport_mean
                    )
                    time_by_transport_mean.append(minutes)
                except Exception as e:
                    self.logger.debug(f"Erreur calcul trajet ({transport_mean}): {e}")
                    continue
            
            return min(time_by_transport_mean) if time_by_transport_mean else 1000
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul du temps de trajet: {e}")
            return 1000
    
    async def score_jobs_parallel(
        self,
        cv_data: CVData,
        jobs: List[Dict],
        max_workers: int = None
    ) -> List[Dict]:
        """
        Score plusieurs offres en parallèle pour améliorer les performances
        
        Args:
            cv_data: Données du CV
            jobs: Liste des offres d'emploi à scorer
            max_workers: Nombre maximum de workers parallèles (défaut: settings.max_parallel_scoring)
            
        Returns:
            Liste des offres scorées triées par score décroissant
        """
        if not jobs:
            return []
        
        max_workers = max_workers or settings.max_parallel_scoring
        semaphore = asyncio.Semaphore(max_workers)
        
        async def score_with_limit(job: Dict) -> Dict:
            """Score une offre avec limitation de concurrence"""
            async with semaphore:
                try:
                    # Calculer la distance
                    distance = await self.get_best_travel_time(job, cv_data)
                    
                    # Scorer avec le LLM
                    scored_job = await self.score_job(cv_data, job, distance)
                    return scored_job
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement de l'offre {job.get('job_id')}: {e}")
                    # Retourner l'offre avec score 0 en cas d'erreur
                    job_filtered = select_from_job(job)
                    job_filtered["score"] = 0
                    job_filtered["distance_between_cities"] = 1000
                    return job_filtered
        
        self.logger.info(f"Scoring de {len(jobs)} offres en parallèle (max {max_workers} workers)")
        
        # Créer toutes les tâches
        tasks = [score_with_limit(job) for job in jobs]
        
        # Exécuter en parallèle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les erreurs et trier par score
        scored_jobs = [
            result for result in results
            if isinstance(result, dict) and not isinstance(result, Exception)
        ]
        
        # Trier par score décroissant
        scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        self.logger.info(f"Scoring terminé: {len(scored_jobs)} offres scorées avec succès")
        
        return scored_jobs

