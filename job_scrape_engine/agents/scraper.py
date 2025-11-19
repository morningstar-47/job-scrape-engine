"""Job scraper agent for collecting job listings from various platforms."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import aiohttp
from bs4 import BeautifulSoup

from .base import BaseAgent
from ..models.job import Job, JobStatus


class ScraperAgent(BaseAgent):
    """Agent responsible for scraping job listings from various platforms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the scraper agent.
        
        Args:
            config: Configuration containing platforms and scraping rules
        """
        super().__init__("ScraperAgent", config)
        self.platforms = self.config.get("platforms", [])
        self.max_concurrent_requests = self.config.get("max_concurrent_requests", 5)
    
    async def process(self, platform_urls: List[str]) -> List[Job]:
        """
        Scrape job listings from the provided platform URLs.
        
        Args:
            platform_urls: List of URLs to scrape
            
        Returns:
            List of scraped Job objects
        """
        self.logger.info(f"Starting scraping process for {len(platform_urls)} URLs")
        
        jobs = []
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._scrape_url(session, url, semaphore)
                for url in platform_urls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Scraping error: {result}")
                elif result:
                    jobs.extend(result)
        
        self.logger.info(f"Scraped {len(jobs)} jobs successfully")
        return jobs
    
    async def _scrape_url(
        self, 
        session: aiohttp.ClientSession, 
        url: str,
        semaphore: asyncio.Semaphore
    ) -> List[Job]:
        """
        Scrape a single URL for job listings.
        
        Args:
            session: aiohttp session
            url: URL to scrape
            semaphore: Semaphore for rate limiting
            
        Returns:
            List of Job objects found at the URL
        """
        async with semaphore:
            try:
                self.logger.info(f"Scraping URL: {url}")
                
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        self.logger.warning(f"Failed to fetch {url}: status {response.status}")
                        return []
                    
                    html = await response.text()
                    return self._parse_html(html, url)
                    
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                return []
    
    def _parse_html(self, html: str, source_url: str) -> List[Job]:
        """
        Parse HTML to extract job listings.
        
        Args:
            html: HTML content
            source_url: Source URL of the HTML
            
        Returns:
            List of parsed Job objects
        """
        soup = BeautifulSoup(html, 'lxml')
        jobs = []
        
        # Generic parsing - in real implementation, this would be platform-specific
        # This is a simplified example that demonstrates the structure
        job_elements = soup.find_all('article', class_='job-listing') or soup.find_all('div', class_='job')
        
        for idx, element in enumerate(job_elements):
            try:
                job = self._extract_job_from_element(element, source_url, idx)
                if job:
                    jobs.append(job)
            except Exception as e:
                self.logger.error(f"Error parsing job element: {e}")
        
        return jobs
    
    def _extract_job_from_element(
        self, 
        element: Any, 
        source_url: str,
        idx: int
    ) -> Optional[Job]:
        """
        Extract job data from a single HTML element.
        
        Args:
            element: BeautifulSoup element
            source_url: Source URL
            idx: Index of the job element
            
        Returns:
            Job object or None if extraction fails
        """
        try:
            # Generic extraction - real implementation would be platform-specific
            title_elem = element.find(['h2', 'h3', 'a'], class_=['title', 'job-title'])
            company_elem = element.find(['span', 'div'], class_=['company', 'company-name'])
            description_elem = element.find(['div', 'p'], class_=['description', 'job-description'])
            
            if not title_elem:
                return None
            
            job = Job(
                external_id=f"{source_url}_{idx}",
                title=title_elem.get_text(strip=True),
                company=company_elem.get_text(strip=True) if company_elem else "Unknown",
                description=description_elem.get_text(strip=True) if description_elem else "",
                url=source_url,
                source_platform=self._extract_platform_name(source_url),
                status=JobStatus.NEW,
                scraped_date=datetime.now(timezone.utc),
                raw_data={
                    "html": str(element),
                    "source_url": source_url,
                }
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error extracting job from element: {e}")
            return None
    
    def _extract_platform_name(self, url: str) -> str:
        """
        Extract platform name from URL.
        
        Args:
            url: URL to extract platform from
            
        Returns:
            Platform name
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain.split('.')[0] if domain else "unknown"
