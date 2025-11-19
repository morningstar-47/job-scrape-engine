"""Example script demonstrating the job scraping system."""

import asyncio
from job_scrape_engine.orchestrator import JobScrapingOrchestrator
from job_scrape_engine.config import get_default_config


async def main():
    """Run an example job scraping pipeline."""
    
    print("=== Job Scraping Engine Demo ===\n")
    
    # Get default configuration
    config = get_default_config()
    
    # Customize configuration for demo
    config["scraper"]["max_concurrent_requests"] = 3
    config["responder"]["auto_respond"] = False
    
    # Initialize orchestrator
    orchestrator = JobScrapingOrchestrator(config)
    
    # Example URLs (these are fake URLs for demonstration)
    # In a real scenario, these would be actual job board URLs
    example_urls = [
        "https://example-jobs.com/python-developer",
        "https://example-jobs.com/frontend-engineer",
        "https://example-jobs.com/data-scientist",
    ]
    
    print(f"Starting pipeline with {len(example_urls)} URLs...\n")
    
    try:
        # Run the complete pipeline
        results = await orchestrator.run_pipeline(example_urls)
        
        # Display results
        print("\n=== Results ===")
        print(f"URLs processed: {results['urls_processed']}")
        print(f"Jobs scraped: {results['jobs_scraped']}")
        print(f"Jobs normalized: {results['jobs_normalized']}")
        print(f"Jobs stored: {results['jobs_stored']}")
        print(f"Responses generated: {results['responses_generated']}")
        print(f"Execution time: {results['execution_time_seconds']} seconds")
        
        # Display response details
        if results.get('responses'):
            print("\n=== Response Details ===")
            for i, response_data in enumerate(results['responses'], 1):
                job = response_data['job']
                should_respond = response_data.get('should_respond', False)
                
                print(f"\n{i}. {job.title} at {job.company}")
                print(f"   Status: {job.status}")
                print(f"   Should respond: {should_respond}")
                
                if should_respond:
                    response = response_data.get('response')
                    if response:
                        print(f"   Response subject: {response.subject}")
        
        print("\n=== Demo completed successfully! ===")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
