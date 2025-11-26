"""Chargeur de templates avec cache"""
from pathlib import Path
from functools import lru_cache
from app.config.settings import settings


class TemplateLoader:
    """Charge et cache les templates de prompts"""
    
    def __init__(self, template_dir: Path = None):
        self.template_dir = template_dir or settings.template_dir
    
    @lru_cache(maxsize=10)
    def load(self, filename: str) -> str:
        """
        Charge un template avec cache
        
        Args:
            filename: Nom du fichier template
            
        Returns:
            Contenu du template
            
        Raises:
            FileNotFoundError: Si le template n'existe pas
        """
        template_path = self.template_dir / filename
        if not template_path.exists():
            raise FileNotFoundError(f"Template {filename} introuvable dans {self.template_dir}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()


# Instance globale du chargeur de templates
template_loader = TemplateLoader()

