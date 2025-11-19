"""Responder agent for automated job application responses."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re

from .base import BaseAgent
from ..models.job import Job, JobStatus
from ..models.response import ResponseTemplate, JobResponse, ResponseStatus


class ResponderAgent(BaseAgent):
    """Agent responsible for generating and sending automated responses to job listings."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the responder agent.
        
        Args:
            config: Configuration containing response templates and settings
        """
        super().__init__("ResponderAgent", config)
        self.templates = self._load_templates()
        self.auto_respond = self.config.get("auto_respond", False)
        self.response_criteria = self.config.get("response_criteria", {})
    
    async def process(self, jobs: List[Job]) -> List[Dict[str, Any]]:
        """
        Process jobs and generate responses.
        
        Args:
            jobs: List of jobs to process for responses
            
        Returns:
            List of dictionaries containing job and response information
        """
        self.logger.info(f"Starting response generation for {len(jobs)} jobs")
        
        results = []
        for job in jobs:
            try:
                result = await self._process_job(job)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing job {job.id}: {e}")
                results.append({
                    "job": job,
                    "response": None,
                    "error": str(e),
                })
        
        self.logger.info(f"Generated {len(results)} responses")
        return results
    
    async def _process_job(self, job: Job) -> Dict[str, Any]:
        """
        Process a single job and generate response if criteria met.
        
        Args:
            job: Job to process
            
        Returns:
            Dictionary with job and response information
        """
        # Check if job meets response criteria
        if not self._meets_criteria(job):
            self.logger.debug(f"Job {job.id} does not meet response criteria")
            return {
                "job": job,
                "response": None,
                "should_respond": False,
                "reason": "Does not meet criteria",
            }
        
        # Select appropriate template
        template = self._select_template(job)
        if not template:
            self.logger.warning(f"No template found for job {job.id}")
            return {
                "job": job,
                "response": None,
                "should_respond": False,
                "reason": "No template available",
            }
        
        # Generate response
        response = self._generate_response(job, template)
        
        # Update job status
        job.status = JobStatus.RESPONDED
        
        result = {
            "job": job,
            "response": response,
            "should_respond": True,
            "auto_sent": False,
        }
        
        # If auto-respond is enabled, simulate sending
        if self.auto_respond:
            response.status = ResponseStatus.SENT
            response.sent_date = datetime.now(timezone.utc)
            result["auto_sent"] = True
            self.logger.info(f"Auto-responded to job {job.id}")
        
        return result
    
    def _meets_criteria(self, job: Job) -> bool:
        """
        Check if a job meets the response criteria.
        
        Args:
            job: Job to check
            
        Returns:
            True if job meets criteria, False otherwise
        """
        criteria = self.response_criteria
        
        # Check required skills match
        if "required_skills" in criteria:
            required = set(criteria["required_skills"])
            job_skills = set(job.required_skills)
            if not required.intersection(job_skills):
                return False
        
        # Check job type
        if "job_types" in criteria:
            if job.job_type not in criteria["job_types"]:
                return False
        
        # Check remote type
        if "remote_types" in criteria:
            if job.remote_type not in criteria["remote_types"]:
                return False
        
        # Check salary minimum
        if "min_salary" in criteria and job.salary_min:
            if job.salary_min < criteria["min_salary"]:
                return False
        
        # Check location
        if "locations" in criteria and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in criteria["locations"]
            )
            if not location_match:
                return False
        
        return True
    
    def _select_template(self, job: Job) -> Optional[ResponseTemplate]:
        """
        Select the most appropriate response template for a job.
        
        Args:
            job: Job to select template for
            
        Returns:
            Selected ResponseTemplate or None
        """
        if not self.templates:
            return None
        
        # For now, return the first template
        # In a real implementation, this would use more sophisticated matching
        return self.templates[0] if self.templates else None
    
    def _generate_response(self, job: Job, template: ResponseTemplate) -> JobResponse:
        """
        Generate a response from a template.
        
        Args:
            job: Job to respond to
            template: Response template to use
            
        Returns:
            JobResponse object
        """
        # Prepare variables for template substitution
        variables = {
            "job_title": job.title,
            "company": job.company,
            "location": job.location or "N/A",
            "job_type": job.job_type or "N/A",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        
        # Add any custom variables from config
        variables.update(self.config.get("custom_variables", {}))
        
        # Substitute variables in subject and body
        subject = self._substitute_variables(template.subject, variables)
        body = self._substitute_variables(template.body, variables)
        
        # Create response object
        response = JobResponse(
            job_id=job.id or "",
            template_id=template.id,
            subject=subject,
            body=body,
            status=ResponseStatus.PENDING,
            metadata={
                "template_name": template.name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        return response
    
    def _substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """
        Substitute variables in text.
        
        Args:
            text: Text with variable placeholders
            variables: Dictionary of variable values
            
        Returns:
            Text with variables substituted
        """
        result = text
        for key, value in variables.items():
            # Replace {variable_name} with value
            pattern = r'\{' + re.escape(key) + r'\}'
            result = re.sub(pattern, str(value), result)
        
        return result
    
    def _load_templates(self) -> List[ResponseTemplate]:
        """
        Load response templates from configuration.
        
        Returns:
            List of ResponseTemplate objects
        """
        templates = []
        template_configs = self.config.get("templates", [])
        
        if not template_configs:
            # Add a default template
            template_configs = [{
                "name": "Default Application",
                "subject": "Application for {job_title} at {company}",
                "body": """Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}.

I believe my skills and experience make me a strong candidate for this role. I am particularly interested in this opportunity because of {company}'s reputation and the exciting challenges this position offers.

I would welcome the opportunity to discuss how I can contribute to your team.

Thank you for your consideration.

Best regards,
[Your Name]
""",
            }]
        
        for config in template_configs:
            template = ResponseTemplate(
                name=config["name"],
                subject=config["subject"],
                body=config["body"],
                variables=config.get("variables", {}),
            )
            templates.append(template)
        
        self.logger.info(f"Loaded {len(templates)} response templates")
        return templates
