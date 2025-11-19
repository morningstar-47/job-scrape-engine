"""Orchestrator for coordinating all agents in the job scraping system."""

import asyncio
import logging
from typing import List, Dict, Any, Optional

from .agents import ScraperAgent, NormalizerAgent, StorageAgent, ResponderAgent
from .models.job import Job


class JobScrapingOrchestrator:
    """
    Orchestrator that coordinates all agents in the job scraping pipeline.
    
    Pipeline: Scraping -> Normalization -> Storage -> Response
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config: Configuration dictionary for all agents
        """
        self.config = config or {}
        self.logger = logging.getLogger("orchestrator")
        self._setup_logging()
        
        # Initialize agents
        self.scraper = ScraperAgent(self.config.get("scraper", {}))
        self.normalizer = NormalizerAgent(self.config.get("normalizer", {}))
        self.storage = StorageAgent(self.config.get("storage", {}))
        self.responder = ResponderAgent(self.config.get("responder", {}))
        
        self.logger.info("JobScrapingOrchestrator initialized")
    
    def _setup_logging(self) -> None:
        """Set up logging for the orchestrator."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def run_pipeline(self, urls: List[str]) -> Dict[str, Any]:
        """
        Run the complete job scraping pipeline.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dictionary with pipeline results and statistics
        """
        self.logger.info(f"Starting pipeline for {len(urls)} URLs")
        start_time = asyncio.get_event_loop().time()
        
        results = {
            "urls_processed": len(urls),
            "jobs_scraped": 0,
            "jobs_normalized": 0,
            "jobs_stored": 0,
            "responses_generated": 0,
            "errors": [],
        }
        
        try:
            # Step 1: Scraping
            self.logger.info("Step 1: Scraping jobs")
            jobs = await self.scraper.process(urls)
            results["jobs_scraped"] = len(jobs)
            
            if not jobs:
                self.logger.warning("No jobs scraped, pipeline stopped")
                # Add execution time before returning
                end_time = asyncio.get_event_loop().time()
                results["execution_time_seconds"] = round(end_time - start_time, 2)
                return results
            
            # Step 2: Normalization
            self.logger.info("Step 2: Normalizing jobs")
            normalized_jobs = await self.normalizer.process(jobs)
            results["jobs_normalized"] = len(normalized_jobs)
            
            # Step 3: Storage
            self.logger.info("Step 3: Storing jobs")
            stored_jobs = await self.storage.process(normalized_jobs)
            results["jobs_stored"] = len(stored_jobs)
            
            # Step 4: Response generation
            self.logger.info("Step 4: Generating responses")
            responses = await self.responder.process(stored_jobs)
            results["responses_generated"] = len([r for r in responses if r.get("should_respond")])
            results["responses"] = responses
            
            # Calculate execution time
            end_time = asyncio.get_event_loop().time()
            results["execution_time_seconds"] = round(end_time - start_time, 2)
            
            self.logger.info(f"Pipeline completed successfully in {results['execution_time_seconds']}s")
            
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
            results["errors"].append(str(e))
            raise
        
        return results
    
    async def scrape_only(self, urls: List[str]) -> List[Job]:
        """
        Run only the scraping step.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraped jobs
        """
        self.logger.info("Running scrape-only mode")
        return await self.scraper.process(urls)
    
    async def normalize_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Run only the normalization step.
        
        Args:
            jobs: List of jobs to normalize
            
        Returns:
            List of normalized jobs
        """
        self.logger.info("Running normalize-only mode")
        return await self.normalizer.process(jobs)
    
    async def store_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Run only the storage step.
        
        Args:
            jobs: List of jobs to store
            
        Returns:
            List of stored jobs
        """
        self.logger.info("Running store-only mode")
        return await self.storage.process(jobs)
    
    async def generate_responses(self, jobs: List[Job]) -> List[Dict[str, Any]]:
        """
        Run only the response generation step.
        
        Args:
            jobs: List of jobs to generate responses for
            
        Returns:
            List of response results
        """
        self.logger.info("Running response-only mode")
        return await self.responder.process(jobs)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of all agents.
        
        Returns:
            Dictionary with status of all agents
        """
        return {
            "orchestrator": "active",
            "agents": {
                "scraper": self.scraper.get_status(),
                "normalizer": self.normalizer.get_status(),
                "storage": self.storage.get_status(),
                "responder": self.responder.get_status(),
            }
        }
