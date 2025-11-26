"""Service pour l'extraction et le traitement des CV"""
import json
import asyncio
from pathlib import Path
from typing import Union
from groq import Groq

from app.models.cv import CVData
from app.config.settings import settings
from app.utils.template_loader import template_loader
from app.utils.logger import logger
from cv_reader import read_cv, ask_vision


class CVService:
    """Service pour l'extraction de données CV"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.logger = logger
    
    async def extract_from_file(
        self, 
        file_path: Path, 
        file_ext: str
    ) -> CVData:
        """
        Extrait les données d'un CV depuis un fichier
        
        Args:
            file_path: Chemin vers le fichier CV
            file_ext: Extension du fichier (.pdf, .docx, .png, etc.)
            
        Returns:
            CVData: Données extraites du CV
        """
        try:
            if file_ext.lower() in [".pdf", ".docx"]:
                cv_result = await asyncio.to_thread(read_cv, str(file_path))
                cv_dict = json.loads(cv_result)
            elif file_ext.lower() in [".png", ".jpg", ".jpeg"]:
                cv_result = await asyncio.to_thread(ask_vision, str(file_path))
                cv_dict = cv_result
            else:
                raise ValueError(f"Format non supporté: {file_ext}")
            
            # Convertir en modèle CVData avec normalisation
            cv_data = CVData.from_dict(cv_dict)
            
            self.logger.info(f"CV extrait avec succès: {cv_data.title} - {cv_data.address_city}")
            return cv_data
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction du CV: {e}")
            raise

