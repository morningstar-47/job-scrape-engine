"""Storage agent for persisting job data."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import sqlite3
from pathlib import Path

from .base import BaseAgent
from ..models.job import Job, JobStatus


class StorageAgent(BaseAgent):
    """Agent responsible for storing job data in a database."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the storage agent.
        
        Args:
            config: Configuration containing database settings
        """
        super().__init__("StorageAgent", config)
        self.db_path = self.config.get("db_path", "jobs.db")
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database and create tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                external_id TEXT UNIQUE,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                url TEXT,
                source_platform TEXT,
                salary_min REAL,
                salary_max REAL,
                salary_currency TEXT,
                job_type TEXT,
                remote_type TEXT,
                experience_level TEXT,
                required_skills TEXT,
                preferred_skills TEXT,
                requirements TEXT,
                posted_date TEXT,
                scraped_date TEXT,
                deadline TEXT,
                status TEXT,
                raw_data TEXT,
                normalized_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on external_id for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_id ON jobs(external_id)
        """)
        
        # Create index on status for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
        """)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Database initialized at {self.db_path}")
    
    async def process(self, jobs: List[Job]) -> List[Job]:
        """
        Store jobs in the database.
        
        Args:
            jobs: List of jobs to store
            
        Returns:
            List of stored Job objects with updated IDs and status
        """
        self.logger.info(f"Starting storage for {len(jobs)} jobs")
        
        stored_jobs = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for job in jobs:
                try:
                    stored_job = await self._store_job(cursor, job)
                    stored_jobs.append(stored_job)
                except Exception as e:
                    self.logger.error(f"Error storing job {job.external_id}: {e}")
                    job.status = JobStatus.ERROR
                    stored_jobs.append(job)
            
            conn.commit()
            self.logger.info(f"Stored {len(stored_jobs)} jobs successfully")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error in storage process: {e}")
            raise
        finally:
            conn.close()
        
        return stored_jobs
    
    async def _store_job(self, cursor: sqlite3.Cursor, job: Job) -> Job:
        """
        Store a single job in the database.
        
        Args:
            cursor: Database cursor
            job: Job to store
            
        Returns:
            Stored Job object with updated ID and status
        """
        # Generate ID if not present
        if not job.id:
            job.id = self._generate_job_id(job)
        
        # Check if job already exists
        cursor.execute("SELECT id FROM jobs WHERE external_id = ?", (job.external_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing job
            self._update_job(cursor, job)
            self.logger.debug(f"Updated existing job: {job.external_id}")
        else:
            # Insert new job
            self._insert_job(cursor, job)
            self.logger.debug(f"Inserted new job: {job.external_id}")
        
        job.status = JobStatus.STORED
        return job
    
    def _insert_job(self, cursor: sqlite3.Cursor, job: Job) -> None:
        """Insert a new job into the database."""
        cursor.execute("""
            INSERT INTO jobs (
                id, external_id, title, company, location, description, url,
                source_platform, salary_min, salary_max, salary_currency,
                job_type, remote_type, experience_level, required_skills,
                preferred_skills, requirements, posted_date, scraped_date,
                deadline, status, raw_data, normalized_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.id,
            job.external_id,
            job.title,
            job.company,
            job.location,
            job.description,
            str(job.url) if job.url else None,
            job.source_platform,
            job.salary_min,
            job.salary_max,
            job.salary_currency,
            job.job_type,
            job.remote_type,
            job.experience_level,
            json.dumps(job.required_skills),
            json.dumps(job.preferred_skills),
            job.requirements,
            job.posted_date.isoformat() if job.posted_date else None,
            job.scraped_date.isoformat(),
            job.deadline.isoformat() if job.deadline else None,
            job.status,
            json.dumps(job.raw_data),
            json.dumps(job.normalized_data),
        ))
    
    def _update_job(self, cursor: sqlite3.Cursor, job: Job) -> None:
        """Update an existing job in the database."""
        cursor.execute("""
            UPDATE jobs SET
                title = ?, company = ?, location = ?, description = ?,
                url = ?, source_platform = ?, salary_min = ?, salary_max = ?,
                salary_currency = ?, job_type = ?, remote_type = ?,
                experience_level = ?, required_skills = ?, preferred_skills = ?,
                requirements = ?, posted_date = ?, scraped_date = ?, deadline = ?,
                status = ?, raw_data = ?, normalized_data = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE external_id = ?
        """, (
            job.title,
            job.company,
            job.location,
            job.description,
            str(job.url) if job.url else None,
            job.source_platform,
            job.salary_min,
            job.salary_max,
            job.salary_currency,
            job.job_type,
            job.remote_type,
            job.experience_level,
            json.dumps(job.required_skills),
            json.dumps(job.preferred_skills),
            job.requirements,
            job.posted_date.isoformat() if job.posted_date else None,
            job.scraped_date.isoformat(),
            job.deadline.isoformat() if job.deadline else None,
            job.status,
            json.dumps(job.raw_data),
            json.dumps(job.normalized_data),
            job.external_id,
        ))
    
    def _generate_job_id(self, job: Job) -> str:
        """
        Generate a unique ID for a job.
        
        Args:
            job: Job to generate ID for
            
        Returns:
            Generated job ID
        """
        import hashlib
        
        # Create ID from external_id and scraped_date
        id_string = f"{job.external_id}_{job.scraped_date.isoformat()}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    async def get_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        """
        Retrieve jobs from the database.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to retrieve
            offset: Offset for pagination
            
        Returns:
            List of Job objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute("""
                    SELECT * FROM jobs WHERE status = ?
                    ORDER BY scraped_date DESC LIMIT ? OFFSET ?
                """, (status, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM jobs
                    ORDER BY scraped_date DESC LIMIT ? OFFSET ?
                """, (limit, offset))
            
            rows = cursor.fetchall()
            jobs = [self._row_to_job(row) for row in rows]
            
            return jobs
            
        finally:
            conn.close()
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """
        Convert a database row to a Job object.
        
        Args:
            row: Database row
            
        Returns:
            Job object
        """
        return Job(
            id=row['id'],
            external_id=row['external_id'],
            title=row['title'],
            company=row['company'],
            location=row['location'],
            description=row['description'],
            url=row['url'],
            source_platform=row['source_platform'],
            salary_min=row['salary_min'],
            salary_max=row['salary_max'],
            salary_currency=row['salary_currency'],
            job_type=row['job_type'],
            remote_type=row['remote_type'],
            experience_level=row['experience_level'],
            required_skills=json.loads(row['required_skills']) if row['required_skills'] else [],
            preferred_skills=json.loads(row['preferred_skills']) if row['preferred_skills'] else [],
            requirements=row['requirements'],
            posted_date=datetime.fromisoformat(row['posted_date']) if row['posted_date'] else None,
            scraped_date=datetime.fromisoformat(row['scraped_date']),
            deadline=datetime.fromisoformat(row['deadline']) if row['deadline'] else None,
            status=row['status'],
            raw_data=json.loads(row['raw_data']) if row['raw_data'] else {},
            normalized_data=json.loads(row['normalized_data']) if row['normalized_data'] else {},
        )
