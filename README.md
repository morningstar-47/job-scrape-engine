# Job Scrape Engine

A multi-agent system designed to automate the process of collecting, normalizing, storing, and responding to job offers. The system uses multiple specialized agents to efficiently process data and interact with external platforms.

## Overview

Job Scrape Engine is a comprehensive solution for automating job search processes. It consists of four specialized agents that work together in a coordinated pipeline:

1. **Scraper Agent** - Collects job listings from various job platforms
2. **Normalizer Agent** - Standardizes and enriches job data
3. **Storage Agent** - Persists job information in a database
4. **Responder Agent** - Generates and manages automated responses to job listings

## Features

- **Multi-Agent Architecture**: Specialized agents for different tasks
- **Async Processing**: High-performance asynchronous operations
- **Data Normalization**: Automatic extraction of skills, salary, location, and remote type
- **Flexible Storage**: SQLite database with easy querying
- **Smart Filtering**: Configurable criteria for automated responses
- **Template System**: Customizable response templates
- **CLI Interface**: Easy-to-use command-line interface
- **Extensible Design**: Easy to add new platforms and features

## Installation

### Using pip

```bash
pip install -e .
```

### For development

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Initialize Configuration

```bash
job-scraper config init -o config.json
```

This creates a default configuration file that you can customize.

### 2. Run the Pipeline

```bash
job-scraper run https://example-jobs.com/python-developer https://example-jobs.com/data-scientist
```

### 3. Check System Status

```bash
job-scraper status
```

## Usage

### Python API

```python
import asyncio
from job_scrape_engine.orchestrator import JobScrapingOrchestrator
from job_scrape_engine.config import get_default_config

async def main():
    # Get configuration
    config = get_default_config()
    
    # Initialize orchestrator
    orchestrator = JobScrapingOrchestrator(config)
    
    # Run pipeline
    urls = [
        "https://example.com/job1",
        "https://example.com/job2",
    ]
    
    results = await orchestrator.run_pipeline(urls)
    
    print(f"Jobs scraped: {results['jobs_scraped']}")
    print(f"Jobs stored: {results['jobs_stored']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Command-Line Interface

#### Run the full pipeline

```bash
job-scraper run <urls...> [--config CONFIG] [--output OUTPUT]
```

#### Show configuration

```bash
job-scraper config show
```

#### Initialize configuration file

```bash
job-scraper config init --output config.json
```

## Configuration

The system uses a JSON configuration file with the following structure:

```json
{
  "scraper": {
    "platforms": ["linkedin", "indeed", "glassdoor"],
    "max_concurrent_requests": 5
  },
  "normalizer": {
    "extract_skills": true,
    "extract_salary": true,
    "normalize_location": true
  },
  "storage": {
    "db_path": "data/jobs.db",
    "backup_enabled": false
  },
  "responder": {
    "auto_respond": false,
    "response_criteria": {
      "required_skills": ["Python", "JavaScript"],
      "job_types": ["full-time", "contract"],
      "remote_types": ["remote", "hybrid"],
      "min_salary": 50000
    },
    "templates": [
      {
        "name": "Default Application",
        "subject": "Application for {job_title} at {company}",
        "body": "Dear Hiring Manager, ..."
      }
    ]
  }
}
```

## Architecture

### Agent Pipeline

```
URLs → Scraper → Normalizer → Storage → Responder → Results
```

### Scraper Agent

- Collects job listings from provided URLs
- Supports concurrent requests for better performance
- Handles errors gracefully
- Extracts basic job information

### Normalizer Agent

- Cleans and standardizes text fields
- Extracts skills from job descriptions
- Identifies salary information
- Determines remote work type
- Normalizes job types and locations

### Storage Agent

- Persists jobs to SQLite database
- Handles duplicate jobs (updates existing entries)
- Provides querying capabilities
- Maintains job history

### Responder Agent

- Evaluates jobs against response criteria
- Generates personalized responses from templates
- Supports template variables
- Can auto-send responses (when configured)

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=job_scrape_engine --cov-report=html
```

Run specific tests:

```bash
pytest tests/agents/test_normalizer.py
```

## Example

See `example.py` for a complete working example:

```bash
python example.py
```

## Development

### Project Structure

```
job-scrape-engine/
├── job_scrape_engine/
│   ├── agents/
│   │   ├── base.py
│   │   ├── scraper.py
│   │   ├── normalizer.py
│   │   ├── storage.py
│   │   └── responder.py
│   ├── config/
│   │   └── config_loader.py
│   ├── models/
│   │   ├── job.py
│   │   └── response.py
│   ├── cli.py
│   └── orchestrator.py
├── tests/
│   ├── agents/
│   ├── models/
│   └── conftest.py
├── example.py
├── requirements.txt
└── setup.py
```

### Adding New Platforms

To add support for a new job platform:

1. Extend the `ScraperAgent` with platform-specific parsing logic
2. Add platform configuration to your config file
3. Implement platform-specific HTML parsing in `_parse_html` method

### Extending Agents

All agents inherit from `BaseAgent` and implement the `process` method:

```python
from job_scrape_engine.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__("CustomAgent", config)
    
    async def process(self, data):
        # Your custom logic here
        return processed_data
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with:
- Python 3.8+
- aiohttp for async HTTP requests
- BeautifulSoup4 for HTML parsing
- Pydantic for data validation
- SQLite for data storage
