"""Command-line interface for the job scraping system."""

import asyncio
import argparse
import json
import sys
from pathlib import Path

from .orchestrator import JobScrapingOrchestrator
from .config import load_config, get_default_config, save_config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-agent job scraping system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the job scraping pipeline")
    run_parser.add_argument(
        "urls",
        nargs="+",
        help="URLs to scrape for jobs"
    )
    run_parser.add_argument(
        "-c", "--config",
        help="Path to configuration file"
    )
    run_parser.add_argument(
        "-o", "--output",
        help="Output file for results (JSON)"
    )
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "action",
        choices=["show", "init"],
        help="Configuration action"
    )
    config_parser.add_argument(
        "-o", "--output",
        help="Output path for config file"
    )
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "run":
        asyncio.run(run_pipeline(args))
    elif args.command == "config":
        handle_config(args)
    elif args.command == "status":
        asyncio.run(show_status(args))


async def run_pipeline(args):
    """Run the job scraping pipeline."""
    config = load_config(args.config)
    orchestrator = JobScrapingOrchestrator(config)
    
    print(f"Starting job scraping for {len(args.urls)} URLs...")
    
    try:
        results = await orchestrator.run_pipeline(args.urls)
        
        print("\n=== Pipeline Results ===")
        print(f"URLs processed: {results['urls_processed']}")
        print(f"Jobs scraped: {results['jobs_scraped']}")
        print(f"Jobs normalized: {results['jobs_normalized']}")
        print(f"Jobs stored: {results['jobs_stored']}")
        print(f"Responses generated: {results['responses_generated']}")
        print(f"Execution time: {results['execution_time_seconds']}s")
        
        if results.get('errors'):
            print(f"\nErrors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Save results to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove response objects for JSON serialization
            save_results = {k: v for k, v in results.items() if k != 'responses'}
            
            with open(args.output, 'w') as f:
                json.dump(save_results, f, indent=2)
            
            print(f"\nResults saved to {args.output}")
        
        print("\nPipeline completed successfully!")
        
    except Exception as e:
        print(f"\nError running pipeline: {e}")
        sys.exit(1)


def handle_config(args):
    """Handle configuration commands."""
    if args.action == "show":
        config = get_default_config()
        print(json.dumps(config, indent=2))
    
    elif args.action == "init":
        output_path = args.output or "config.json"
        config = get_default_config()
        save_config(config, output_path)
        print(f"Configuration saved to {output_path}")


async def show_status(args):
    """Show system status."""
    config = load_config(None)
    orchestrator = JobScrapingOrchestrator(config)
    
    status = orchestrator.get_status()
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
