"""Configuration loader for the job scraping system."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file or return default config.
    
    Args:
        config_path: Path to configuration file (JSON)
        
    Returns:
        Configuration dictionary
    """
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Try to load from environment variable
    env_config = os.getenv("JOB_SCRAPER_CONFIG")
    if env_config and Path(env_config).exists():
        with open(env_config, 'r') as f:
            return json.load(f)
    
    # Return default configuration
    return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for the job scraping system.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "scraper": {
            "platforms": [
                "linkedin",
                "indeed",
                "glassdoor",
            ],
            "max_concurrent_requests": 5,
        },
        "normalizer": {
            "extract_skills": True,
            "extract_salary": True,
            "normalize_location": True,
        },
        "storage": {
            "db_path": "data/jobs.db",
            "backup_enabled": False,
        },
        "responder": {
            "auto_respond": False,
            "response_criteria": {
                "required_skills": ["Python", "JavaScript"],
                "job_types": ["full-time", "contract"],
                "remote_types": ["remote", "hybrid"],
                "min_salary": 50000,
            },
            "templates": [
                {
                    "name": "Default Application",
                    "subject": "Application for {job_title} at {company}",
                    "body": """Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}.

I believe my skills and experience make me a strong candidate for this role. I am particularly interested in this opportunity because of {company}'s reputation and the exciting challenges this position offers.

I would welcome the opportunity to discuss how I can contribute to your team.

Thank you for your consideration.

Best regards,
[Your Name]
""",
                }
            ],
            "custom_variables": {
                "your_name": "Job Seeker",
                "your_email": "jobseeker@example.com",
            },
        },
    }


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
    """
    # Create parent directories if they don't exist
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
