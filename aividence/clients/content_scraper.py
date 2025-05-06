"""ContentScraper client for loading content from websites or HTML files."""
import os
import re
import time
import random
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from aividence.config import DEFAULT_HEADERS, CONTENT_SCRAPER_TIMEOUT

logger = logging.getLogger("FactCheckTool.ContentScraper")

class ContentScraper:
    """A class to load website content from URLs or HTML files using multiple fallback methods."""
    
    def __init__(self, user_agent=None, timeout=CONTENT_SCRAPER_TIMEOUT, verbose=False):
        """Initialize the scraper with configurable parameters."""
        self.timeout = timeout
        self.verbose = verbose
        
        # Default user agent that resembles a normal browser
        self.user_agent = user_agent or DEFAULT_HEADERS['User-Agent']
        self.headers = DEFAULT_HEADERS.copy()
        self.headers['User-Agent'] = self.user_agent
    
    def _get_domain(self, url):
        """Extract the domain from a URL."""
        parsed_url = urlparse(url)
        return parsed_url.netloc
    
    def _log(self, message):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            logger.info(message)
    
    def _load_with_requests(self, url):
        """Attempt to load the website using the requests library."""
        self._log(f"Trying to load URL with requests: {url}")
        
        try:
            # Add a small random delay to appear more human-like
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(
                url, 
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Check if we received HTML content
                if 'text/html' in content_type:
                    self._log(f"Successfully loaded URL with requests: {len(response.text)} bytes")
                    return response.text
                else:
                    self._log(f"Received non-HTML content: {content_type}")
            
            return None
            
        except requests.exceptions.RequestException as e:
            self._log(f"Request failed: {str(e)}")
            return None
    
    def _load_with_selenium(self, url):
        """Attempt to load the website using Selenium with Chrome."""
        self._log(f"Trying to load URL with Selenium: {url}")
        
        driver = None
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={self.user_agent}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Initialize the driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            
            # Navigate to the URL
            driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for any JavaScript to execute
            time.sleep(5)
            
            # Get the page source
            html_content = driver.page_source
            
            self._log(f"Successfully loaded URL with Selenium: {len(html_content)} bytes")
            return html_content
            
        except (TimeoutException, WebDriverException) as e:
            self._log(f"Selenium loading failed: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def _load_from_html_file(self, file_path):
        """Load content from a local HTML file."""
        self._log(f"Loading content from HTML file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                
            self._log(f"Successfully loaded HTML file: {len(html_content)} bytes")
            return html_content
        except Exception as e:
            self._log(f"Error loading HTML file: {str(e)}")
            raise ValueError(f"Could not load content from HTML file: {file_path}")
    
    def _check_for_access_denial(self, content):
        """Check if the content indicates access denial or bot detection."""
        if not content:
            return False
            
        lower_content = content.lower()
        
        # Common phrases indicating access denial
        denial_indicators = [
            "access denied",
            "access to this page has been denied",
            "has been blocked",
            "detected unusual activity",
            "please enable javascript",
            "browser appears to have javascript disabled",
            "captcha",
            "cloudflare",
            "ddos protection",
            "human verification",
            "bot protection",
            "security check"
        ]
        
        for indicator in denial_indicators:
            if indicator in lower_content:
                self._log(f"Access denial detected: '{indicator}'")
                return True
                
        return False
    
    def _extract_main_content(self, html_content):
        """
        Extract the main content from HTML, skipping navigation,
        headers, footers, and other non-essential elements.
        """
        if not html_content:
            return ""
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Try to find the main content
            main_content = None
            
            # Try common main content containers
            for container in ["main", "article", ".content", "#content", ".main", "#main"]:
                if container.startswith(".") or container.startswith("#"):
                    main_content = soup.select_one(container)
                else:
                    main_content = soup.find(container)
                    
                if main_content:
                    break
            
            # If no specific container found, use the body
            if not main_content:
                main_content = soup.body
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                return text
            else:
                # Fallback to full page text
                return soup.get_text(separator='\n', strip=True)
                
        except Exception as e:
            self._log(f"Error extracting main content: {str(e)}")
            
            # Fallback to returning the original HTML
            return html_content
    
    def _is_html_file(self, path):
        """Check if the given path is pointing to an HTML file."""
        # Check if it's a file path (not a URL) and has an HTML extension
        return os.path.isfile(path) and path.lower().endswith(('.html', '.htm'))
    
    def _is_valid_url(self, url):
        """Check if the given string is a valid URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def load_content(self, source, source_type=None):
        """
        Load content from either a website URL or an HTML file.
        
        Args:
            source: The URL of the website or path to HTML file
            source_type: Optional type specifier ('url' or 'file'). If None, type is auto-detected.
            
        Returns:
            str: The website content as text
        
        Raises:
            ValueError: If the content could not be loaded after all attempts
        """
        # Auto-detect source type if not specified
        if source_type is None:
            if self._is_html_file(source):
                source_type = 'file'
            elif self._is_valid_url(source):
                source_type = 'url'
            else:
                raise ValueError(f"Could not determine if '{source}' is a URL or HTML file. Please specify source_type.")
        
        if source_type.lower() == 'file':
            self._log(f"Loading content from HTML file: {source}")
            content = self._load_from_html_file(source)
        elif source_type.lower() == 'url':
            self._log(f"Loading content from URL: {source}")
            # Try with standard requests first
            content = self._load_with_requests(source)
            
            # Check if we got meaningful content or if it looks like we hit a protection page
            if not content or self._check_for_access_denial(content):
                self._log("Standard request failed or hit access denial, trying with Selenium")
                content = self._load_with_selenium(source)
            
            # If we still don't have content or still hit a protection page
            if not content or self._check_for_access_denial(content):
                raise ValueError(f"Could not load content from URL: {source} after multiple attempts")
        else:
            raise ValueError(f"Invalid source_type: {source_type}. Must be 'url' or 'file'.")
        
        # Extract the main content
        extracted_content = self._extract_main_content(content)
        
        self._log(f"Successfully extracted {len(extracted_content)} characters of content")
        return extracted_content
    
    # Maintain backward compatibility
    def load_website_content(self, url):
        """
        Legacy method to maintain backward compatibility.
        
        Args:
            url: The URL of the website to load
            
        Returns:
            str: The website content as text
        """
        return self.load_content(url, source_type='url')