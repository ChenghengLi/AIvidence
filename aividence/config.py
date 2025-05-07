"""Configuration module for the fact checking tool."""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
# This needs to be at the top of the file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO if os.environ.get("VERBOSE", "0") != "1" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AIvidence")

# API keys from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")

# Check for required API keys
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not set. Some functionality may be limited.")
if not ANTHROPIC_API_KEY:
    logger.warning("Anthropic API key not set. Some functionality may be limited.")
if not BRAVE_API_KEY:
    logger.warning("Brave Search API key not set. Web search functionality will be limited.")

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
DEFAULT_MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")  # Updated default from .env
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", 5))  # Get from .env or use default

# Verbose logging
VERBOSE = os.environ.get("VERBOSE", "0") == "1"  # Convert string to boolean

# Additional configuration options
# These can be expanded as needed based on future .env settings
def get_config_summary():
    """Return a summary of the current configuration for logging purposes."""
    return {
        "Model": DEFAULT_MODEL_NAME,
        "Max Claims": DEFAULT_MAX_CLAIMS,
        "Verbose": VERBOSE,
        "OpenAI API Key": "Set" if OPENAI_API_KEY else "Not Set",
        "Anthropic API Key": "Set" if ANTHROPIC_API_KEY else "Not Set",
        "Brave API Key": "Set" if BRAVE_API_KEY else "Not Set"
    }

# Log configuration on import
if VERBOSE:
    logger.debug(f"Configuration loaded: {get_config_summary()}")