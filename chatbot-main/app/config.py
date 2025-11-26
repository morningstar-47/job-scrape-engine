"""
Configuration de l'application
Gère le chargement des variables d'environnement et les paramètres de l'application
"""
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))
    
    # Application Configuration
    app_name: str = os.getenv("APP_NAME", "Job Engine - Chatbot Assistant")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    app_description: str = os.getenv("APP_DESCRIPTION", "Assistant virtuel polyvalent avec LangChain, OpenAI et RAG pour la gestion de la base de connaissances et des recherches d'emploi")
    # ChromaDB Configuration
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    # RAG Configuration
    retriever_k: int = int(os.getenv("RETRIEVER_K", "4"))  # Nombre de documents à récupérer
    
    # RapidAPI Configuration
    rapidapi_key: str = os.getenv("RAPIDAPI_KEY", "")
    
    # Sessions Database Configuration
    sessions_db_path: str = os.getenv("SESSIONS_DB_PATH", "./sessions.db")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instance globale des paramètres
settings = Settings()


def get_settings() -> Settings:
    """Retourne l'instance des paramètres"""
    return settings

