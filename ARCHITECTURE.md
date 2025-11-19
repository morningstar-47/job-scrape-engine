# Job Scrape Engine - Architecture Documentation

## System Overview

Job Scrape Engine is a multi-agent system designed to automate the job search process through a pipeline of specialized agents.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Job Scraping Orchestrator                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            Agent Pipeline                            │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │   Scraper    │ ───▶ │  Normalizer  │ ───▶ │   Storage    │ ───▶ │  Responder   │
    │    Agent     │      │    Agent     │      │    Agent     │      │    Agent     │
    └──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
         │                      │                     │                      │
         ▼                      ▼                     ▼                      ▼
    Web Scraping          Data Cleaning         SQLite Database      Email/Response
    (aiohttp +           Skill Extraction        Job Storage         Generation
    BeautifulSoup)       Salary Parsing          Deduplication       Template System
```

## Component Details

### 1. Scraper Agent
**Purpose**: Collect job listings from various job platforms

**Key Features**:
- Asynchronous web scraping using aiohttp
- Concurrent request handling with rate limiting
- HTML parsing with BeautifulSoup4
- Platform-agnostic design (extensible to multiple job boards)

**Input**: List of URLs to scrape
**Output**: List of raw Job objects

**Code Location**: `job_scrape_engine/agents/scraper.py`

### 2. Normalizer Agent
**Purpose**: Standardize and enrich job data

**Key Features**:
- Text normalization (whitespace, formatting)
- Skill extraction using pattern matching
- Salary information parsing (ranges, currencies)
- Job type classification (full-time, part-time, contract)
- Remote work type detection (remote, hybrid, on-site)
- Location normalization

**Input**: List of raw Job objects
**Output**: List of normalized Job objects

**Code Location**: `job_scrape_engine/agents/normalizer.py`

### 3. Storage Agent
**Purpose**: Persist job data to a database

**Key Features**:
- SQLite database integration
- Automatic deduplication based on external_id
- Job history tracking
- Efficient querying and filtering
- Update handling for existing jobs

**Input**: List of normalized Job objects
**Output**: List of stored Job objects with database IDs

**Code Location**: `job_scrape_engine/agents/storage.py`

### 4. Responder Agent
**Purpose**: Generate and manage automated responses to job listings

**Key Features**:
- Template-based response generation
- Configurable response criteria (skills, salary, location, job type)
- Variable substitution in templates
- Optional auto-send functionality
- Response tracking and status management

**Input**: List of stored Job objects
**Output**: List of response results with generated messages

**Code Location**: `job_scrape_engine/agents/responder.py`

## Data Models

### Job Model
```python
class Job:
    - id: Unique identifier
    - external_id: Source platform identifier
    - title: Job title
    - company: Company name
    - location: Job location
    - description: Full job description
    - url: Source URL
    - source_platform: Platform name
    - salary_min/max: Salary range
    - job_type: Employment type
    - remote_type: Remote work option
    - required_skills: List of required skills
    - status: Current processing status
    - raw_data: Original scraped data
    - normalized_data: Processing metadata
```

### Response Models
```python
class ResponseTemplate:
    - name: Template name
    - subject: Email subject
    - body: Email body with variables
    - variables: Custom variable definitions

class JobResponse:
    - job_id: Associated job ID
    - template_id: Template used
    - subject: Generated subject
    - body: Generated body
    - status: Response status
    - sent_date: Timestamp if sent
```

## Configuration System

Configuration is managed through JSON files with the following structure:

```json
{
  "scraper": {
    "platforms": ["linkedin", "indeed", "glassdoor"],
    "max_concurrent_requests": 5
  },
  "normalizer": {
    "extract_skills": true,
    "extract_salary": true
  },
  "storage": {
    "db_path": "data/jobs.db"
  },
  "responder": {
    "auto_respond": false,
    "response_criteria": {
      "required_skills": ["Python", "JavaScript"],
      "job_types": ["full-time"],
      "remote_types": ["remote", "hybrid"],
      "min_salary": 50000
    },
    "templates": [...]
  }
}
```

## Orchestrator

The `JobScrapingOrchestrator` coordinates all agents in the pipeline:

1. Initializes all agents with configuration
2. Manages data flow between agents
3. Handles errors and exceptions
4. Provides pipeline statistics and monitoring
5. Supports partial pipeline execution (scrape-only, normalize-only, etc.)

**Code Location**: `job_scrape_engine/orchestrator.py`

## CLI Interface

Command-line interface for easy system interaction:

```bash
# Run full pipeline
job-scraper run <urls...>

# Initialize configuration
job-scraper config init

# Show configuration
job-scraper config show

# Check system status
job-scraper status
```

**Code Location**: `job_scrape_engine/cli.py`

## Extension Points

### Adding New Job Platforms

To add support for a new job platform:

1. Add platform-specific parsing logic to `ScraperAgent._parse_html()`
2. Update configuration with platform name
3. Implement platform-specific selectors

### Custom Normalizers

To add custom normalization logic:

1. Extend `NormalizerAgent` class
2. Override or add new extraction methods
3. Update skill patterns or job type mappings

### Response Templates

To add new response templates:

1. Define template in configuration JSON
2. Use `{variable_name}` syntax for substitution
3. Add custom variables in config

## Testing Strategy

The system includes comprehensive tests:

- **Unit Tests**: Test individual agent functionality
- **Integration Tests**: Test agent interactions
- **Model Tests**: Validate data models
- **Coverage**: 67% code coverage across the system

Test files are organized to mirror the source structure:
```
tests/
├── agents/          # Agent-specific tests
├── models/          # Model validation tests
└── conftest.py      # Shared test fixtures
```

## Security Considerations

1. **Input Validation**: All URLs and data are validated before processing
2. **SQL Injection Prevention**: Parameterized queries used throughout
3. **Rate Limiting**: Prevents overwhelming target servers
4. **Error Handling**: Graceful failure handling for network errors
5. **Data Privacy**: No sensitive data logged or exposed

## Performance

- **Async Processing**: Non-blocking I/O for web requests
- **Concurrent Scraping**: Multiple URLs processed simultaneously
- **Database Indexing**: Optimized queries with indexes on key fields
- **Memory Efficient**: Streaming data processing where possible

## Future Enhancements

Potential areas for extension:

1. **Additional Platforms**: LinkedIn, Indeed, Glassdoor integrations
2. **AI-Powered Matching**: ML-based job matching algorithms
3. **Email Integration**: Direct email sending via SMTP
4. **Web Dashboard**: Browser-based monitoring interface
5. **Job Alerts**: Real-time notifications for matching jobs
6. **Resume Parser**: Extract skills from resume for better matching
7. **API Server**: REST API for programmatic access
8. **Cloud Storage**: Support for cloud databases (PostgreSQL, MongoDB)

## Dependencies

- **Python 3.8+**: Core language
- **aiohttp**: Async HTTP requests
- **BeautifulSoup4**: HTML parsing
- **Pydantic**: Data validation
- **SQLite**: Local database
- **pytest**: Testing framework

## Deployment

For production deployment:

1. Set up virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Configure via JSON file or environment variables
4. Run via CLI or import as Python module
5. Set up cron jobs for scheduled scraping

## Support and Maintenance

- **Logging**: Comprehensive logging at all levels
- **Error Tracking**: Detailed error messages and stack traces
- **Status Monitoring**: Real-time agent status reporting
- **Diagnostics**: Built-in health checks and status endpoints
