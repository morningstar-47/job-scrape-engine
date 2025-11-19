"""Normalizer agent for standardizing job data."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .base import BaseAgent
from ..models.job import Job, JobStatus


class NormalizerAgent(BaseAgent):
    """Agent responsible for normalizing and standardizing job data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the normalizer agent.
        
        Args:
            config: Configuration containing normalization rules
        """
        super().__init__("NormalizerAgent", config)
        self.skill_patterns = self._load_skill_patterns()
        self.job_type_mappings = self._load_job_type_mappings()
    
    async def process(self, jobs: List[Job]) -> List[Job]:
        """
        Normalize a list of jobs.
        
        Args:
            jobs: List of jobs to normalize
            
        Returns:
            List of normalized Job objects
        """
        self.logger.info(f"Starting normalization for {len(jobs)} jobs")
        
        normalized_jobs = []
        for job in jobs:
            try:
                normalized_job = await self._normalize_job(job)
                normalized_jobs.append(normalized_job)
            except Exception as e:
                self.logger.error(f"Error normalizing job {job.external_id}: {e}")
                job.status = JobStatus.ERROR
                normalized_jobs.append(job)
        
        self.logger.info(f"Normalized {len(normalized_jobs)} jobs successfully")
        return normalized_jobs
    
    async def _normalize_job(self, job: Job) -> Job:
        """
        Normalize a single job.
        
        Args:
            job: Job to normalize
            
        Returns:
            Normalized Job object
        """
        # Normalize text fields
        job.title = self._normalize_text(job.title)
        job.company = self._normalize_text(job.company)
        job.description = self._normalize_text(job.description)
        
        # Extract skills from description
        if job.description:
            skills = self._extract_skills(job.description)
            job.required_skills = list(set(job.required_skills + skills))
        
        # Normalize job type
        job.job_type = self._normalize_job_type(job.job_type or "", job.description)
        
        # Extract salary information if present in description
        if not job.salary_min or not job.salary_max:
            salary_info = self._extract_salary(job.description)
            if salary_info:
                job.salary_min = salary_info.get("min")
                job.salary_max = salary_info.get("max")
                job.salary_currency = salary_info.get("currency", "USD")
        
        # Normalize location
        if job.location:
            job.location = self._normalize_location(job.location)
        
        # Extract remote type
        job.remote_type = self._extract_remote_type(job.description, job.title)
        
        # Update status and metadata
        job.status = JobStatus.NORMALIZED
        job.normalized_data = {
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "skills_extracted": len(job.required_skills),
            "has_salary": bool(job.salary_min or job.salary_max),
        }
        
        return job
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by cleaning whitespace and formatting.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_skills(self, description: str) -> List[str]:
        """
        Extract skills from job description.
        
        Args:
            description: Job description
            
        Returns:
            List of extracted skills
        """
        skills = []
        description_lower = description.lower()
        
        for skill, patterns in self.skill_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    skills.append(skill)
                    break
        
        return skills
    
    def _normalize_job_type(self, job_type: str, description: str) -> str:
        """
        Normalize job type (full-time, part-time, contract, etc.).
        
        Args:
            job_type: Original job type
            description: Job description for context
            
        Returns:
            Normalized job type
        """
        job_type_lower = job_type.lower()
        description_lower = description.lower()
        
        for normalized, patterns in self.job_type_mappings.items():
            for pattern in patterns:
                if pattern in job_type_lower or pattern in description_lower:
                    return normalized
        
        return "full-time"  # Default
    
    def _extract_salary(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Extract salary information from description.
        
        Args:
            description: Job description
            
        Returns:
            Dictionary with salary information or None
        """
        # Pattern for salary ranges (e.g., $50,000 - $70,000, 50k-70k)
        patterns = [
            r'\$?([\d,]+)k?\s*-\s*\$?([\d,]+)k?',
            r'([\d,]+)\s*€\s*-\s*([\d,]+)\s*€',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    min_sal = float(match.group(1).replace(',', ''))
                    max_sal = float(match.group(2).replace(',', ''))
                    
                    # If values look like they're in thousands (e.g., "50k")
                    if 'k' in description[match.start():match.end()].lower():
                        min_sal *= 1000
                        max_sal *= 1000
                    
                    currency = "USD"
                    if "€" in description[match.start():match.end()]:
                        currency = "EUR"
                    
                    return {
                        "min": min_sal,
                        "max": max_sal,
                        "currency": currency,
                    }
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _normalize_location(self, location: str) -> str:
        """
        Normalize location string.
        
        Args:
            location: Location string
            
        Returns:
            Normalized location
        """
        location = self._normalize_text(location)
        
        # Remove common prefixes/suffixes
        location = re.sub(r'^(location:?|lieu:?)\s*', '', location, flags=re.IGNORECASE)
        
        return location
    
    def _extract_remote_type(self, description: str, title: str) -> str:
        """
        Extract remote work type from description and title.
        
        Args:
            description: Job description
            title: Job title
            
        Returns:
            Remote type: "remote", "hybrid", or "on-site"
        """
        combined_text = f"{title} {description}".lower()
        
        if any(word in combined_text for word in ['remote', 'télétravail', 'work from home', 'wfh']):
            if any(word in combined_text for word in ['hybrid', 'hybride', 'part-time remote']):
                return "hybrid"
            return "remote"
        
        return "on-site"
    
    def _load_skill_patterns(self) -> Dict[str, List[str]]:
        """
        Load skill patterns for extraction.
        
        Returns:
            Dictionary mapping skills to regex patterns
        """
        return {
            "Python": [r'\bpython\b', r'\bdjango\b', r'\bflask\b', r'\bfastapi\b'],
            "JavaScript": [r'\bjavascript\b', r'\bjs\b', r'\bnode\.?js\b', r'\breact\b', r'\bvue\b', r'\bangular\b'],
            "Java": [r'\bjava\b', r'\bspring\b'],
            "SQL": [r'\bsql\b', r'\bmysql\b', r'\bpostgresql\b', r'\bpostgres\b'],
            "Docker": [r'\bdocker\b', r'\bkubernetes\b', r'\bk8s\b'],
            "AWS": [r'\baws\b', r'\bamazon web services\b', r'\bec2\b', r'\bs3\b'],
            "Git": [r'\bgit\b', r'\bgithub\b', r'\bgitlab\b'],
            "CI/CD": [r'\bci/cd\b', r'\bjenkins\b', r'\bgithub actions\b', r'\bgitlab ci\b'],
        }
    
    def _load_job_type_mappings(self) -> Dict[str, List[str]]:
        """
        Load job type mappings for normalization.
        
        Returns:
            Dictionary mapping normalized types to pattern lists
        """
        return {
            "full-time": ["full-time", "full time", "temps plein", "cdi"],
            "part-time": ["part-time", "part time", "temps partiel"],
            "contract": ["contract", "contractor", "freelance", "contrat"],
            "internship": ["internship", "intern", "stage"],
            "temporary": ["temporary", "temp", "temporaire", "cdd"],
        }
