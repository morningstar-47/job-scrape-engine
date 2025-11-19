"""Data models for job scraping system."""

from .job import Job, JobStatus
from .response import ResponseTemplate, ResponseStatus

__all__ = ["Job", "JobStatus", "ResponseTemplate", "ResponseStatus"]
