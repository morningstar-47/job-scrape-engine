"""Configuration du système de logging"""
import logging
import sys
from pathlib import Path
from app.config.settings import settings


def setup_logger(name: str = "api_job", log_file: Path = None) -> logging.Logger:
    """
    Configure et retourne un logger structuré
    
    Args:
        name: Nom du logger
        log_file: Chemin optionnel vers un fichier de log
        
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Éviter les handlers dupliqués
    if logger.handlers:
        return logger
    
    # Niveau de log selon l'environnement
    log_level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(log_level)
    
    # Format structuré
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optionnel)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Logger global
logger = setup_logger()

