"""Configuration centralisée de l'application avec Pydantic Settings"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # API Keys
    groq_api_key: str = Field(..., min_length=10, description="Clé API Groq")
    job_scrapper_api_key: str = Field(..., min_length=10, description="Clé API RapidAPI JSearch")
    google_maps_api_key: str = Field(default="", description="Clé API Google Maps (optionnel)")
    
    # LLM Models
    cv_extraction_model: str = Field(
        default="openai/gpt-oss-20b",
        description="Modèle pour l'extraction de données CV"
    )
    image_analysis_model: str = Field(
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        description="Modèle pour l'analyse d'images CV"
    )
    job_scoring_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Modèle pour le scoring des offres"
    )
    query_generation_model: str = Field(
        default="openai/gpt-oss-20b",
        description="Modèle pour la génération de requêtes"
    )
    
    # Limits
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Taille maximale des fichiers uploadés"
    )
    max_jobs_to_score: int = Field(
        default=50,
        description="Nombre maximum d'offres à scorer"
    )
    max_parallel_scoring: int = Field(
        default=5,
        description="Nombre maximum d'offres à scorer en parallèle"
    )
    
    # Paths
    template_dir: Path = Field(
        default=Path(__file__).parent.parent.parent / "template_prompt",
        description="Répertoire des templates de prompts"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        description="Origines autorisées pour CORS"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Environnement d'exécution"
    )
    debug: bool = Field(
        default=False,
        description="Mode debug"
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Valide que l'environnement est valide"""
        if v not in ['development', 'staging', 'production']:
            raise ValueError('Environment must be development, staging or production')
        return v
    
    @field_validator('template_dir')
    @classmethod
    def validate_template_dir(cls, v: Path) -> Path:
        """Valide que le répertoire des templates existe"""
        if not v.exists():
            raise ValueError(f"Template directory {v} does not exist")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instance globale de la configuration
settings = Settings()

