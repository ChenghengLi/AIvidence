"""Command-line interface for running the fact checking tool."""
import os
import re
import argparse
import logging
from typing import Tuple, Optional

from aividence.config import (
    DEFAULT_MODEL_NAME, 
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    BRAVE_API_KEY,
    DEFAULT_MAX_CLAIMS,
    logger
)
from aividence.core.fact_check_engine import FactCheckEngine
from aividence.models.content_analysis_report import ContentAnalysisReport

def setup_argparser() -> argparse.ArgumentParser:
    """Set up the argument parser for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Analyze websites or HTML files for misinformation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Source arguments
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--url", "-u",
        help="URL of the website to analyze"
    )
    source_group.add_argument(
        "--file", "-f",
        help="Path to an HTML file to analyze"
    )
    
    # Model arguments
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL_NAME,
        help="Language model to use for analysis (e.g., gpt-3.5-turbo, claude-3-sonnet-20240229)"
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for the model API (for Ollama models)"
    )

    # Add this to the setup_argparser function
    parser.add_argument(
        "--output-dir", "-d",
        default="reports",
        help="Directory where reports will be saved"
    )
        
    # API key arguments (can also be set via environment variables)
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key (overrides environment variable)"
    )
    parser.add_argument(
        "--anthropic-key",
        help="Anthropic API key (overrides environment variable)"
    )
    parser.add_argument(
        "--brave-key",
        help="Brave Search API key (overrides environment variable)"
    )
    
    # Analysis configuration
    parser.add_argument(
        "--max-claims", "-c",
        type=int,
        default=DEFAULT_MAX_CLAIMS,
        help="Maximum number of claims to verify"
    )
    parser.add_argument(
        "--output", "-o",
        default="report.md",
        help="Output file for the markdown report"
    )
    
    # Debug options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser

def get_api_keys(args: argparse.Namespace) -> Tuple[Optional[str], Optional[str], str]:
    """
    Get API keys from command-line arguments or environment variables.
    
    Args:
        args: Command-line arguments
    
    Returns:
        Tuple of (openai_api_key, anthropic_api_key, brave_api_key)
    """
    # OpenAI API key
    openai_key = args.openai_key if args.openai_key else OPENAI_API_KEY
    
    # Anthropic API key
    anthropic_key = args.anthropic_key if args.anthropic_key else ANTHROPIC_API_KEY
    
    # Brave Search API key
    brave_key = args.brave_key if args.brave_key else BRAVE_API_KEY
    
    return openai_key, anthropic_key, brave_key

def get_model_api_key(model_name: str, openai_key: Optional[str], anthropic_key: Optional[str]) -> Optional[str]:
    """
    Get the appropriate API key for the specified model.
    
    Args:
        model_name: Name of the model
        openai_key: OpenAI API key
        anthropic_key: Anthropic API key
    
    Returns:
        The appropriate API key or None
    """
    if "gpt" in model_name.lower() or "openai" in model_name.lower():
        return openai_key
    elif "claude" in model_name.lower() or "anthropic" in model_name.lower():
        return anthropic_key
    else:
        return None  # For Ollama models, no API key needed

def run_fact_check(source: str, source_type: Optional[str] = None, 
                  model_name: str = DEFAULT_MODEL_NAME, api_key: Optional[str] = None, 
                  base_url: Optional[str] = None, brave_api_key: str = BRAVE_API_KEY, 
                  max_claims: int = DEFAULT_MAX_CLAIMS, output_file: str = "report.md", 
                  output_dir: str = "reports", verbose: bool = False) -> Tuple[Optional[ContentAnalysisReport], Optional[str]]:
    """
    Analyze content from a URL or HTML file for misinformation.
    
    Args:
        source: URL of the website or path to HTML file to analyze
        source_type: Type of source ('url' or 'file'). If None, type is auto-detected.
        model_name: LLM model to use
        api_key: API key for the LLM service
        base_url: Base URL for the LLM service (used with Ollama models)
        brave_api_key: API key for Brave Search
        max_claims: Maximum number of claims to verify
        output_file: Output file for the markdown report
        verbose: Enable verbose logging
        
    Returns:
        Tuple of (content_analysis_result, markdown_report)
    """
    # Initialize the engine
    engine = FactCheckEngine(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        brave_api_key=brave_api_key,
        verbose=verbose
    )
    
    try:
        # Auto-detect source type if not specified
        if source_type is None:
            if os.path.isfile(source) and source.lower().endswith(('.html', '.htm')):
                source_type = 'file'
                if verbose:
                    logger.info(f"Auto-detected source type: HTML file")
            elif re.match(r'^https?://', source):
                source_type = 'url'
                if verbose:
                    logger.info(f"Auto-detected source type: URL")
            else:
                raise ValueError(f"Could not determine if '{source}' is a URL or HTML file. Please specify source_type.")
        
        # Analyze the content
        result = engine.analyze_content(source, source_type, max_claims)
        
        # Generate markdown report
        report = result.to_markdown_report()

        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, output_file)
        
        # Save to file with UTF-8 encoding to handle all characters
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"Analysis complete! Report saved to {output_path}")
        
        # Print summary to console
        print("\n" + "-" * 80)
        print(f"Source: {result.domain}")
        print(f"Topic: {result.topic}")
        print(f"Overall Score: {result.overall_score}/5")
        print("-" * 80 + "\n")
        print(result.summary)
        
        # Print recency warning if needed
        recent_claims = [r for r in result.verification_results if r.is_recent_news]
        if recent_claims:
            print("\n" + "-" * 80)
            print("WARNING: This analysis contains claims about recent events.")
            print("Information available online may be limited or still evolving.")
            print("Results should be interpreted with caution and reevaluated as more information becomes available.")
            print("-" * 80)
            
        print("\n" + "-" * 80)
        
        return result, report
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        print(f"Error: {str(e)}")
        return None, None

def main():
    """Main entry point for the command-line interface."""
    parser = setup_argparser()
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    
    # Get API keys
    openai_key, anthropic_key, brave_key = get_api_keys(args)
    
    # Determine source and source type
    source = args.url if args.url else args.file
    source_type = 'url' if args.url else 'file'
    
    # Get the appropriate API key for the model
    api_key = get_model_api_key(args.model, openai_key, anthropic_key)
    
    # Run the analysis
    run_fact_check(
        source=source,
        source_type=source_type,
        model_name=args.model,
        api_key=api_key,
        base_url=args.base_url,
        brave_api_key=brave_key,
        max_claims=args.max_claims,
        output_file=args.output,
        output_dir=args.output_dir,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()