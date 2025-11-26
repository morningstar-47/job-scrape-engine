"""Service pour la génération de requêtes de recherche"""
import json
from typing import Dict

from app.models.cv import CVData
from app.config.settings import settings
from app.utils.template_loader import template_loader
from app.utils.logger import logger
from groq import Groq


class QueryService:
    """Service pour générer des requêtes de recherche optimisées"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.logger = logger
    
    async def generate_search_query(self, cv_data: CVData) -> str:
        """
        Génère une requête de recherche optimale avec un LLM
        
        Args:
            cv_data: Données du CV
            
        Returns:
            Requête de recherche (ex: "comptabilité Paris")
        """
        try:
            prompt_template = template_loader.load("prompt_query_generator.txt")
            
            # Construire le résumé du CV pour le LLM
            experiences = cv_data.experience[:3] if cv_data.experience else []
            
            cv_summary = {
                "titre_cv": cv_data.title,
                "ville": cv_data.address_city,
                "pays": cv_data.address_country,
                "resume": cv_data.summary[:300] if cv_data.summary else "",
                "competences_techniques": cv_data.skills.technical[:8],
                "experiences_professionnelles": [
                    {
                        "poste": exp.title,
                        "entreprise": exp.company,
                        "periode": f"{exp.period.start or ''} - {exp.period.end or ''}",
                        "missions": exp.missions[:3]
                    }
                    for exp in experiences
                ],
                "mots_cles": cv_data.keywords[:5]
            }
            
            user_prompt = prompt_template + "\n" + json.dumps(cv_summary, ensure_ascii=False, indent=2)
            
            # Appel au LLM
            response = self.groq_client.chat.completions.create(
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
                model=settings.query_generation_model,
                temperature=0.3,
                max_tokens=50
            )
            
            query = response.choices[0].message.content.strip()
            query = query.strip('"').strip("'").strip()
            
            words = query.split()
            
            self.logger.info(f"Requête LLM générée: {query} ({len(words)} mots)")
            
            # Validation
            if not query or len(query) < 3:
                self.logger.warning("Requête LLM vide ou trop courte, utilisation du fallback")
                return self._extract_keywords_fallback(cv_data)
            
            if len(words) > 6:
                self.logger.warning(f"Requête LLM trop longue ({len(words)} mots), utilisation du fallback")
                return self._extract_keywords_fallback(cv_data)
            
            return query
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de la requête: {e}")
            return self._extract_keywords_fallback(cv_data)
    
    def _extract_keywords_fallback(self, cv_data: CVData) -> str:
        """
        Méthode de fallback pour extraire le poste souhaité
        
        Args:
            cv_data: Données du CV
            
        Returns:
            Requête de recherche simplifiée
        """
        # 1. Essayer avec les expériences
        if cv_data.experience:
            job_title = cv_data.experience[0].title
            if job_title and len(job_title.strip()) > 2:
                words = job_title.strip().split()
                if len(words) > 3:
                    job_title = " ".join(words[:3])
                return job_title.lower()
        
        # 2. Mapper le titre du CV
        title_lower = cv_data.title.lower()
        
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
        }
        
        # Chercher un mapping
        for domain, job in domain_mapping.items():
            if domain in title_lower:
                self.logger.info(f"[Mapping] '{domain}' -> '{job}'")
                return job
        
        # 3. Nettoyer le titre
        title_clean = title_lower
        title_clean = title_clean.replace("étudiant", "").replace("étudiante", "")
        title_clean = title_clean.replace("en mastère", "").replace("en master", "")
        title_clean = title_clean.replace("en licence", "").replace("en bachelor", "")
        title_clean = title_clean.strip()
        
        if title_clean:
            words = [w for w in title_clean.split() if len(w) > 3]
            if words:
                return " ".join(words[:2]) if len(words) >= 2 else words[0]
        
        # 4. Utiliser les compétences
        if cv_data.skills.technical:
            return cv_data.skills.technical[0].lower()
        
        return "emploi"

