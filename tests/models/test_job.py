"""Tests for the Job model."""

import pytest
from datetime import datetime
from job_scrape_engine.models.job import Job, JobStatus


def test_job_creation():
    """Test creating a basic job."""
    job = Job(
        title="Software Engineer",
        company="Tech Corp",
        description="Great opportunity",
        source_platform="linkedin",
    )
    
    assert job.title == "Software Engineer"
    assert job.company == "Tech Corp"
    assert job.source_platform == "linkedin"
    assert job.status == JobStatus.NEW
    assert isinstance(job.scraped_date, datetime)


def test_job_with_skills():
    """Test job with skills."""
    job = Job(
        title="Python Developer",
        company="Python Inc",
        description="Python job",
        source_platform="indeed",
        required_skills=["Python", "Django"],
        preferred_skills=["PostgreSQL"],
    )
    
    assert len(job.required_skills) == 2
    assert "Python" in job.required_skills
    assert len(job.preferred_skills) == 1


def test_job_with_salary():
    """Test job with salary information."""
    job = Job(
        title="Data Scientist",
        company="Data Corp",
        description="Data job",
        source_platform="glassdoor",
        salary_min=80000.0,
        salary_max=120000.0,
        salary_currency="USD",
    )
    
    assert job.salary_min == 80000.0
    assert job.salary_max == 120000.0
    assert job.salary_currency == "USD"


def test_job_status_update():
    """Test updating job status."""
    job = Job(
        title="Developer",
        company="Dev Corp",
        description="Dev job",
        source_platform="test",
        status=JobStatus.NEW,
    )
    
    assert job.status == JobStatus.NEW
    
    job.status = JobStatus.NORMALIZED
    assert job.status == JobStatus.NORMALIZED
    
    job.status = JobStatus.STORED
    assert job.status == JobStatus.STORED
