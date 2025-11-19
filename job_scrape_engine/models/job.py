"""Job data model."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class JobStatus(str, Enum):
    """Status of a job listing."""
    NEW = "new"
    NORMALIZED = "normalized"
    STORED = "stored"
    RESPONDED = "responded"
    REJECTED = "rejected"
    ERROR = "error"


class Job(BaseModel):
    """Job listing data model."""
    
    # Unique identifiers
    id: Optional[str] = None
    external_id: Optional[str] = None
    
    # Basic information
    title: str
    company: str
    location: Optional[str] = None
    description: str
    
    # URLs and sources
    url: Optional[HttpUrl] = None
    source_platform: str
    
    # Job details
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    remote_type: Optional[str] = None  # remote, hybrid, on-site
    experience_level: Optional[str] = None
    
    # Requirements and skills
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    requirements: Optional[str] = None
    
    # Dates
    posted_date: Optional[datetime] = None
    scraped_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: Optional[datetime] = None
    
    # Status and metadata
    status: JobStatus = JobStatus.NEW
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    normalized_data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )
