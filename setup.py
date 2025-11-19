"""Setup configuration for the job scraping engine."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="job-scrape-engine",
    version="0.1.0",
    author="Job Scrape Team",
    description="Multi-agent system for automated job collection, normalization, storage, and response",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/morningstar-47/job-scrape-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "sqlalchemy>=2.0.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "job-scraper=job_scrape_engine.cli:main",
        ],
    },
)
