"""Tests for the JobScrapingOrchestrator."""

import pytest
import tempfile
from pathlib import Path
from job_scrape_engine.orchestrator import JobScrapingOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    config = {
        "storage": {
            "db_path": ":memory:",
        }
    }
    orchestrator = JobScrapingOrchestrator(config)
    
    assert orchestrator.scraper is not None
    assert orchestrator.normalizer is not None
    assert orchestrator.storage is not None
    assert orchestrator.responder is not None


@pytest.mark.asyncio
async def test_orchestrator_status():
    """Test getting orchestrator status."""
    config = {
        "storage": {
            "db_path": ":memory:",
        }
    }
    orchestrator = JobScrapingOrchestrator(config)
    
    status = orchestrator.get_status()
    
    assert "orchestrator" in status
    assert "agents" in status
    assert "scraper" in status["agents"]
    assert "normalizer" in status["agents"]
    assert "storage" in status["agents"]
    assert "responder" in status["agents"]


@pytest.mark.asyncio
async def test_orchestrator_scrape_only():
    """Test scrape-only mode."""
    config = {
        "storage": {
            "db_path": ":memory:",
        }
    }
    orchestrator = JobScrapingOrchestrator(config)
    
    # Note: This will fail to scrape real URLs, but tests the flow
    urls = ["https://example.com/jobs"]
    jobs = await orchestrator.scrape_only(urls)
    
    # Empty list expected since we're not hitting real job sites
    assert isinstance(jobs, list)
