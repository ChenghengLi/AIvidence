"""Configuration module for the fact checking tool."""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
# This needs to be at the top of the file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AIvidence")

# API keys from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "123")  # Default placeholder for development

# Default user agent for requests
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# Request headers
DEFAULT_HEADERS = {
    'User-Agent': DEFAULT_USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Brave Search API configuration
BRAVE_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_SEARCH_MAX_RESULTS = 5
BRAVE_SEARCH_TIMEOUT = 10
BRAVE_SEARCH_MAX_RETRIES = 3
BRAVE_SEARCH_RETRY_DELAY = 10

# Content scraper configuration
CONTENT_SCRAPER_TIMEOUT = 30

# Default LLM configuration
DEFAULT_MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_CLAIMS = 5