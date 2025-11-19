"""Tests for the NormalizerAgent."""

import pytest
from job_scrape_engine.agents.normalizer import NormalizerAgent
from job_scrape_engine.models.job import Job, JobStatus


@pytest.mark.asyncio
async def test_normalizer_basic(sample_job):
    """Test basic normalization."""
    agent = NormalizerAgent()
    jobs = await agent.process([sample_job])
    
    assert len(jobs) == 1
    job = jobs[0]
    assert job.status == JobStatus.NORMALIZED
    assert "normalized_at" in job.normalized_data


@pytest.mark.asyncio
async def test_normalizer_skill_extraction():
    """Test skill extraction from description."""
    job = Job(
        external_id="test_1",
        title="Full Stack Developer",
        company="Web Corp",
        description="Looking for developer with Python, JavaScript, React, and Docker experience.",
        source_platform="test",
    )
    
    agent = NormalizerAgent()
    jobs = await agent.process([job])
    
    normalized_job = jobs[0]
    assert len(normalized_job.required_skills) > 0
    # Check if some expected skills were extracted
    skills_found = any(skill in normalized_job.required_skills 
                      for skill in ["Python", "JavaScript", "Docker"])
    assert skills_found


@pytest.mark.asyncio
async def test_normalizer_salary_extraction():
    """Test salary extraction from description."""
    job = Job(
        external_id="test_2",
        title="Software Engineer",
        company="Tech Inc",
        description="Salary range: $80,000 - $120,000 per year. Great benefits.",
        source_platform="test",
    )
    
    agent = NormalizerAgent()
    jobs = await agent.process([job])
    
    normalized_job = jobs[0]
    assert normalized_job.salary_min is not None
    assert normalized_job.salary_max is not None
    assert normalized_job.salary_min < normalized_job.salary_max


@pytest.mark.asyncio
async def test_normalizer_remote_type_extraction():
    """Test remote type extraction."""
    job = Job(
        external_id="test_3",
        title="Remote Python Developer",
        company="Remote Corp",
        description="This is a fully remote position with flexible hours.",
        source_platform="test",
    )
    
    agent = NormalizerAgent()
    jobs = await agent.process([job])
    
    normalized_job = jobs[0]
    assert normalized_job.remote_type in ["remote", "hybrid", "on-site"]


@pytest.mark.asyncio
async def test_normalizer_text_cleaning():
    """Test text normalization and cleaning."""
    job = Job(
        external_id="test_4",
        title="  Software   Engineer  ",
        company="  Tech   Corp  ",
        description="Job   description   with   extra   spaces.",
        source_platform="test",
    )
    
    agent = NormalizerAgent()
    jobs = await agent.process([job])
    
    normalized_job = jobs[0]
    assert normalized_job.title == "Software Engineer"
    assert normalized_job.company == "Tech Corp"
    assert "  " not in normalized_job.description
