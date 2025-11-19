"""Tests for the ResponderAgent."""

import pytest
from job_scrape_engine.agents.responder import ResponderAgent
from job_scrape_engine.models.job import Job, JobStatus
from job_scrape_engine.models.response import ResponseStatus


@pytest.mark.asyncio
async def test_responder_basic():
    """Test basic response generation."""
    agent = ResponderAgent({
        "response_criteria": {
            "required_skills": ["Python"],
        }
    })
    
    job = Job(
        external_id="test_1",
        id="job_1",
        title="Python Developer",
        company="Python Corp",
        description="Looking for Python developer",
        source_platform="test",
        required_skills=["Python"],
    )
    
    results = await agent.process([job])
    
    assert len(results) == 1
    result = results[0]
    assert result["should_respond"] is True
    assert result["response"] is not None


@pytest.mark.asyncio
async def test_responder_criteria_not_met():
    """Test when job doesn't meet response criteria."""
    agent = ResponderAgent({
        "response_criteria": {
            "required_skills": ["Java"],
        }
    })
    
    job = Job(
        external_id="test_2",
        id="job_2",
        title="Python Developer",
        company="Python Corp",
        description="Looking for Python developer",
        source_platform="test",
        required_skills=["Python"],
    )
    
    results = await agent.process([job])
    
    assert len(results) == 1
    result = results[0]
    assert result["should_respond"] is False


@pytest.mark.asyncio
async def test_responder_template_substitution():
    """Test template variable substitution."""
    agent = ResponderAgent({
        "templates": [{
            "name": "Test Template",
            "subject": "Application for {job_title}",
            "body": "Dear {company} team, I'm interested in the {job_title} position.",
        }],
        "response_criteria": {}
    })
    
    job = Job(
        external_id="test_3",
        id="job_3",
        title="Software Engineer",
        company="Tech Corp",
        description="Software engineering position",
        source_platform="test",
    )
    
    results = await agent.process([job])
    
    result = results[0]
    if result["should_respond"]:
        response = result["response"]
        assert "Software Engineer" in response.subject
        assert "Tech Corp" in response.body


@pytest.mark.asyncio
async def test_responder_auto_respond():
    """Test auto-respond feature."""
    agent = ResponderAgent({
        "auto_respond": True,
        "response_criteria": {},
    })
    
    job = Job(
        external_id="test_4",
        id="job_4",
        title="Developer",
        company="Dev Corp",
        description="Developer position",
        source_platform="test",
    )
    
    results = await agent.process([job])
    
    result = results[0]
    if result["should_respond"]:
        assert result["auto_sent"] is True
        response = result["response"]
        assert response.status == ResponseStatus.SENT
        assert response.sent_date is not None


@pytest.mark.asyncio
async def test_responder_job_type_criteria():
    """Test response criteria based on job type."""
    agent = ResponderAgent({
        "response_criteria": {
            "job_types": ["full-time"],
        }
    })
    
    job_fulltime = Job(
        external_id="test_5",
        id="job_5",
        title="Full Time Developer",
        company="Corp A",
        description="Full time position",
        source_platform="test",
        job_type="full-time",
    )
    
    job_parttime = Job(
        external_id="test_6",
        id="job_6",
        title="Part Time Developer",
        company="Corp B",
        description="Part time position",
        source_platform="test",
        job_type="part-time",
    )
    
    results = await agent.process([job_fulltime, job_parttime])
    
    assert results[0]["should_respond"] is True
    assert results[1]["should_respond"] is False
