# Contributing to Job Scrape Engine

Thank you for your interest in contributing to Job Scrape Engine! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Adding New Features](#adding-new-features)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of async/await in Python
- Familiarity with web scraping (for scraper contributions)

### Development Setup

1. **Fork and Clone the Repository**

```bash
git clone https://github.com/your-username/job-scrape-engine.git
cd job-scrape-engine
```

2. **Create a Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
pip install -e ".[dev]"  # Install development dependencies
```

4. **Run Tests**

```bash
pytest
```

## Project Structure

```
job-scrape-engine/
├── job_scrape_engine/       # Main package
│   ├── agents/              # Agent implementations
│   │   ├── base.py         # Base agent class
│   │   ├── scraper.py      # Web scraping agent
│   │   ├── normalizer.py   # Data normalization agent
│   │   ├── storage.py      # Database storage agent
│   │   └── responder.py    # Response generation agent
│   ├── config/             # Configuration management
│   ├── models/             # Data models
│   └── orchestrator.py     # Agent coordination
├── tests/                  # Test suite
├── example.py              # Example usage
└── README.md              # Documentation
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: Maximum 100 characters
- **Imports**: Group in order: standard library, third-party, local
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Google-style docstrings for all public functions

### Example Code Style

```python
"""Module docstring describing the file's purpose."""

from typing import List, Optional
from datetime import datetime

from .base import BaseAgent


class MyAgent(BaseAgent):
    """
    Agent description.
    
    This agent does X, Y, and Z.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("MyAgent", config)
    
    async def process(self, data: List[str]) -> List[str]:
        """
        Process the input data.
        
        Args:
            data: List of strings to process
            
        Returns:
            List of processed strings
        """
        return [item.upper() for item in data]
```

### Linting

Run linting before committing:

```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Type checking
mypy job_scrape_engine
```

## Testing Guidelines

### Writing Tests

1. **Test Files**: Place tests in `tests/` directory, mirroring the source structure
2. **Test Names**: Prefix with `test_` (e.g., `test_scraper_basic()`)
3. **Fixtures**: Use pytest fixtures in `tests/conftest.py` for shared test data
4. **Async Tests**: Mark async tests with `@pytest.mark.asyncio`

### Example Test

```python
import pytest
from job_scrape_engine.agents.normalizer import NormalizerAgent
from job_scrape_engine.models.job import Job


@pytest.mark.asyncio
async def test_normalizer_skill_extraction():
    """Test that normalizer extracts skills correctly."""
    agent = NormalizerAgent()
    
    job = Job(
        title="Python Developer",
        company="Test Corp",
        description="Looking for Python and JavaScript skills",
        source_platform="test",
    )
    
    normalized = await agent.process([job])
    
    assert len(normalized) == 1
    assert "Python" in normalized[0].required_skills
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=job_scrape_engine

# Run specific test file
pytest tests/agents/test_normalizer.py

# Run specific test
pytest tests/agents/test_normalizer.py::test_normalizer_basic

# Run with verbose output
pytest -v
```

### Coverage Requirements

- Aim for at least 80% code coverage for new features
- Critical paths should have 100% coverage
- Check coverage: `pytest --cov=job_scrape_engine --cov-report=html`

## Pull Request Process

### Before Submitting

1. **Create a Branch**

```bash
git checkout -b feature/my-new-feature
```

2. **Make Changes**
   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests**

```bash
pytest
```

4. **Lint Code**

```bash
ruff format .
ruff check .
```

5. **Commit Changes**

```bash
git add .
git commit -m "Add feature: description of changes"
```

### Commit Message Format

Use clear, descriptive commit messages:

```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

Example:
```
feat: Add LinkedIn scraper support

Implement LinkedIn-specific parsing logic in ScraperAgent.
Includes CSS selectors and data extraction for LinkedIn job pages.

Closes #123
```

### Submitting the PR

1. Push your branch: `git push origin feature/my-new-feature`
2. Open a pull request on GitHub
3. Fill out the PR template
4. Link related issues
5. Wait for review

### PR Review Process

- Maintainers will review your code
- Address any requested changes
- Once approved, your PR will be merged

## Adding New Features

### Adding a New Agent

1. **Create Agent Class**

```python
# job_scrape_engine/agents/my_agent.py

from typing import Any
from .base import BaseAgent


class MyAgent(BaseAgent):
    """Description of what this agent does."""
    
    def __init__(self, config=None):
        super().__init__("MyAgent", config)
    
    async def process(self, data: Any) -> Any:
        """Process data through this agent."""
        # Implementation here
        return data
```

2. **Add to `__init__.py`**

```python
# job_scrape_engine/agents/__init__.py

from .my_agent import MyAgent

__all__ = [..., "MyAgent"]
```

3. **Write Tests**

```python
# tests/agents/test_my_agent.py

import pytest
from job_scrape_engine.agents.my_agent import MyAgent


@pytest.mark.asyncio
async def test_my_agent_basic():
    agent = MyAgent()
    result = await agent.process("test data")
    assert result is not None
```

4. **Update Documentation**
   - Add agent description to README.md
   - Update ARCHITECTURE.md with details
   - Add usage examples

### Adding Platform Support

To add support for a new job platform:

1. **Update Scraper Logic**

```python
# In job_scrape_engine/agents/scraper.py

def _parse_html(self, html: str, source_url: str) -> List[Job]:
    """Parse HTML based on platform."""
    platform = self._extract_platform_name(source_url)
    
    if platform == "newplatform":
        return self._parse_newplatform(html, source_url)
    # ... existing platforms
```

2. **Add Platform-Specific Parser**

```python
def _parse_newplatform(self, html: str, source_url: str) -> List[Job]:
    """Parse jobs from New Platform."""
    soup = BeautifulSoup(html, 'lxml')
    jobs = []
    
    # Platform-specific selectors
    job_cards = soup.find_all('div', class_='job-card')
    
    for card in job_cards:
        job = self._extract_newplatform_job(card, source_url)
        if job:
            jobs.append(job)
    
    return jobs
```

3. **Add Tests**

```python
@pytest.mark.asyncio
async def test_scraper_newplatform():
    """Test scraping from New Platform."""
    agent = ScraperAgent()
    
    # Test with mock HTML
    html = """<div class="job-card">...</div>"""
    jobs = agent._parse_html(html, "https://newplatform.com/jobs")
    
    assert len(jobs) > 0
```

### Adding Configuration Options

1. **Update Default Config**

```python
# In job_scrape_engine/config/config_loader.py

def get_default_config():
    return {
        # ... existing config
        "my_agent": {
            "new_option": "default_value",
        }
    }
```

2. **Use in Agent**

```python
class MyAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__("MyAgent", config)
        self.my_option = self.config.get("new_option", "default")
```

3. **Document in README**

Update the configuration section with the new options.

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No debugging code or print statements
- [ ] Type hints are added
- [ ] Docstrings are complete
- [ ] No breaking changes (or clearly documented)
- [ ] Code is performant
- [ ] Error handling is appropriate
- [ ] Logging is meaningful

## Getting Help

- **Documentation**: Check README.md and ARCHITECTURE.md
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for private concerns

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

All contributors will be recognized in the project README. Thank you for helping make Job Scrape Engine better!
