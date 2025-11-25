"""
Service de détection d'intention de recherche d'emploi
Analyse les messages utilisateur pour détecter les demandes de recherche d'emploi
"""
import re
from typing import Dict, Optional, Tuple
from langchain_openai import ChatOpenAI
from app.config import settings


class JobIntentDetector:
    """Détecte les intentions de recherche d'emploi dans les messages"""
    
    def __init__(self):
        """Initialise le détecteur avec un LLM pour l'analyse"""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # Plus bas pour des réponses plus déterministes
            api_key=settings.openai_api_key
        )
        
        # Mots-clés pour détecter une recherche d'emploi
        self.job_keywords = [
            'emploi', 'job', 'travail', 'poste', 'carrière', 'recrutement',
            'cherche', 'recherche', 'offre', 'candidature', 'embauche',
            'développeur', 'ingénieur', 'manager', 'designer', 'analyste'
        ]
    
    def detect_job_search_intent(self, message: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Détecte si le message contient une demande de recherche d'emploi
        
        Args:
            message: Message de l'utilisateur
            
        Returns:
            Tuple (is_job_search, params) où params contient les paramètres extraits
        """
        message_lower = message.lower()
        
        # Vérification rapide avec mots-clés
        has_job_keywords = any(keyword in message_lower for keyword in self.job_keywords)
        
        # Patterns pour détecter les demandes de recherche
        search_patterns = [
            r'(cherche|recherche|trouve|trouver).*?(emploi|job|travail|poste)',
            r'(emploi|job|travail|poste).*?(en|à|dans|pour)',
            r'(offre|offres).*?(emploi|travail)',
            r'(disponible|disponibles).*?(emploi|job|travail)',
        ]
        
        matches_pattern = any(re.search(pattern, message_lower) for pattern in search_patterns)
        
        if not (has_job_keywords or matches_pattern):
            return False, None
        
        # Utiliser le LLM pour extraire les paramètres de manière plus précise
        try:
            extraction_prompt = f"""Analyse ce message utilisateur et détermine s'il s'agit d'une demande de recherche d'emploi.
Si oui, extrais les informations suivantes au format JSON:
- query: le titre du poste ou les compétences recherchées (ex: "développeur Python", "data scientist")
- country: le code pays ISO à 2 lettres si mentionné (ex: "fr" pour France, "de" pour Allemagne, "es" pour Espagne, "it" pour Italie, "be" pour Belgique, "ch" pour Suisse, "ca" pour Canada, "us" pour USA). Si non mentionné, laisse null.
- remote: true si télétravail/remote est mentionné, sinon false
- employment_type: FULLTIME, PARTTIME, CONTRACTOR, ou INTERN si mentionné

Message: "{message}"

Réponds UNIQUEMENT avec un JSON valide, ou "null" si ce n'est pas une recherche d'emploi.
Format attendu: {{"query": "...", "country": "fr", "remote": false, "employment_type": "..."}}
"""
            
            response = self.llm.invoke(extraction_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Nettoyer la réponse pour extraire le JSON
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            if response_text.lower() == 'null' or not response_text:
                return False, None
            
            import json
            params = json.loads(response_text)
            
            if params.get('query'):
                return True, params
            else:
                return False, None
                
        except Exception as e:
            print(f"Erreur lors de la détection d'intention: {e}")
            # Fallback: extraction simple avec regex
            return self._simple_extraction(message)
    
    def _simple_extraction(self, message: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Extraction simple basée sur des patterns regex"""
        message_lower = message.lower()
        
        # Extraire le pays (utiliser les codes ISO pour l'API)
        countries = {
            'france': 'fr', 'french': 'fr', 'paris': 'fr', 'lyon': 'fr',
            'allemagne': 'de', 'germany': 'de', 'berlin': 'de',
            'espagne': 'es', 'spain': 'es', 'madrid': 'es',
            'italie': 'it', 'italy': 'it', 'rome': 'it',
            'belgique': 'be', 'belgium': 'be', 'bruxelles': 'be',
            'suisse': 'ch', 'switzerland': 'ch',
            'canada': 'ca', 'usa': 'us', 'united states': 'us'
        }
        
        country = None
        for key, value in countries.items():
            if key in message_lower:
                country = value
                break
        
        # Détecter télétravail
        remote = 'remote' in message_lower or 'télétravail' in message_lower or 'teletravail' in message_lower
        
        # Extraire le type d'emploi
        employment_type = None
        if 'temps plein' in message_lower or 'fulltime' in message_lower:
            employment_type = 'FULLTIME'
        elif 'temps partiel' in message_lower or 'parttime' in message_lower:
            employment_type = 'PARTTIME'
        elif 'stage' in message_lower or 'intern' in message_lower:
            employment_type = 'INTERN'
        
        # Extraire la requête (mots après "cherche", "recherche", etc.)
        query_match = re.search(r'(cherche|recherche|trouve|trouver|veut|veux).*?(emploi|job|travail|poste).*?((?:développeur|ingénieur|designer|manager|analyste|data|scientist|python|java|javascript|react|vue|angular)[^.]*)', message_lower)
        if query_match:
            query = query_match.group(3).strip()
        else:
            # Essayer d'extraire n'importe quel titre de poste mentionné
            job_titles = ['développeur', 'ingénieur', 'designer', 'manager', 'analyste', 'data scientist', 'python', 'java']
            for title in job_titles:
                if title in message_lower:
                    query = title
                    break
            else:
                query = None
        
        if query:
            params = {
                'query': query,
                'country': country,
                'remote': remote,
                'employment_type': employment_type
            }
            return True, params
        
        return False, None


# Instance globale
job_intent_detector = JobIntentDetector()

