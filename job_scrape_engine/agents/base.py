"""Base agent class for all specialized agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            config: Configuration dictionary for the agent
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging for the agent."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Process data through the agent.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            "name": self.name,
            "status": "active",
            "config": self.config,
        }
