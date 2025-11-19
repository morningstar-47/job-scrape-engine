"""Tests for the StorageAgent."""

import pytest
import tempfile
from pathlib import Path
from job_scrape_engine.agents.storage import StorageAgent
from job_scrape_engine.models.job import Job, JobStatus


@pytest.mark.asyncio
async def test_storage_agent_init():
    """Test storage agent initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        agent = StorageAgent({"db_path": str(db_path)})
        
        assert db_path.exists()


@pytest.mark.asyncio
async def test_storage_save_jobs(sample_jobs):
    """Test saving jobs to database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        agent = StorageAgent({"db_path": str(db_path)})
        
        stored_jobs = await agent.process(sample_jobs)
        
        assert len(stored_jobs) == len(sample_jobs)
        for job in stored_jobs:
            assert job.status == JobStatus.STORED
            assert job.id is not None


@pytest.mark.asyncio
async def test_storage_retrieve_jobs():
    """Test retrieving jobs from database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        agent = StorageAgent({"db_path": str(db_path)})
        
        # Store jobs
        sample_jobs_list = [
            Job(
                external_id=f"job_{i}",
                title=f"Job {i}",
                company=f"Company {i}",
                description=f"Description {i}",
                source_platform="test",
            )
            for i in range(5)
        ]
        await agent.process(sample_jobs_list)
        
        # Retrieve jobs
        retrieved = await agent.get_jobs(limit=10)
        
        assert len(retrieved) == 5


@pytest.mark.asyncio
async def test_storage_duplicate_handling(sample_job):
    """Test handling duplicate jobs (same external_id)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        agent = StorageAgent({"db_path": str(db_path)})
        
        # Store job first time
        await agent.process([sample_job])
        
        # Store same job again (should update)
        sample_job.description = "Updated description"
        await agent.process([sample_job])
        
        # Retrieve and check
        retrieved = await agent.get_jobs()
        assert len(retrieved) == 1
        assert retrieved[0].description == "Updated description"


@pytest.mark.asyncio
async def test_storage_filter_by_status():
    """Test filtering jobs by status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        agent = StorageAgent({"db_path": str(db_path)})
        
        # Create jobs with different statuses
        jobs = [
            Job(
                external_id="job_1",
                title="Job 1",
                company="Company 1",
                description="Desc 1",
                source_platform="test",
                status=JobStatus.STORED,
            ),
            Job(
                external_id="job_2",
                title="Job 2",
                company="Company 2",
                description="Desc 2",
                source_platform="test",
                status=JobStatus.RESPONDED,
            ),
        ]
        
        await agent.process(jobs)
        
        # Filter by status
        stored_jobs = await agent.get_jobs(status=JobStatus.STORED)
        responded_jobs = await agent.get_jobs(status=JobStatus.RESPONDED)
        
        assert len(stored_jobs) == 1
        assert len(responded_jobs) == 1
