"""Response models for automated job applications."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ResponseStatus(str, Enum):
    """Status of a job response/application."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RECEIVED = "received"


class ResponseTemplate(BaseModel):
    """Template for automated job responses."""
    
    id: Optional[str] = None
    name: str
    subject: str
    body: str
    
    # Template variables
    variables: Dict[str, str] = Field(default_factory=dict)
    
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class JobResponse(BaseModel):
    """Record of a response to a job listing."""
    
    id: Optional[str] = None
    job_id: str
    template_id: Optional[str] = None
    
    subject: str
    body: str
    
    status: ResponseStatus = ResponseStatus.PENDING
    sent_date: Optional[datetime] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )
