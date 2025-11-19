"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime, timezone
from job_scrape_engine.models.job import Job, JobStatus


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    return Job(
        external_id="test_job_1",
        title="Senior Python Developer",
        company="Tech Company",
        location="San Francisco, CA",
        description="We are looking for a senior Python developer with 5+ years of experience. Must know Django, Flask, and PostgreSQL.",
        url="https://example.com/jobs/python-dev",
        source_platform="example",
        job_type="full-time",
        remote_type="remote",
        status=JobStatus.NEW,
        scraped_date=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_jobs():
    """Create a list of sample jobs for testing."""
    return [
        Job(
            external_id=f"test_job_{i}",
            title=f"Job Title {i}",
            company=f"Company {i}",
            description=f"Job description {i} with Python and JavaScript skills required.",
            url=f"https://example.com/jobs/{i}",
            source_platform="example",
            status=JobStatus.NEW,
            scraped_date=datetime.now(timezone.utc),
        )
        for i in range(3)
    ]


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return {
        "scraper": {
            "max_concurrent_requests": 2,
        },
        "normalizer": {},
        "storage": {
            "db_path": ":memory:",  # Use in-memory database for tests
        },
        "responder": {
            "auto_respond": False,
            "response_criteria": {
                "required_skills": ["Python"],
            },
        },
    }
