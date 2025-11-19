"""Configuration management for the job scraping system."""

from .config_loader import load_config, get_default_config, save_config

__all__ = ["load_config", "get_default_config", "save_config"]
