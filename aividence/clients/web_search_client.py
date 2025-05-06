"""WebSearchClient for searching the web using Brave Search API."""
import re
import time
import threading
import logging
from typing import List

import requests

from aividence.config import (
    BRAVE_SEARCH_API_URL, 
    BRAVE_SEARCH_MAX_RESULTS,
    BRAVE_SEARCH_TIMEOUT,
    BRAVE_SEARCH_MAX_RETRIES,
    BRAVE_SEARCH_RETRY_DELAY
)
from aividence.models.search_result import SearchResult

logger = logging.getLogger("FactCheckTool.WebSearchClient")

class WebSearchClient:
    """Tool for searching the web using Brave Search API with direct HTTP requests"""
    
    def __init__(self, api_key: str, max_results: int = BRAVE_SEARCH_MAX_RESULTS, 
                 verbose: bool = False, timeout: int = BRAVE_SEARCH_TIMEOUT, 
                 max_retries: int = BRAVE_SEARCH_MAX_RETRIES, 
                 retry_delay: int = BRAVE_SEARCH_RETRY_DELAY):
        """
        Initialize the web search client.
        
        Args:
            api_key: Brave Search API key
            max_results: Maximum number of results to return
            verbose: Whether to enable verbose logging
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.max_results = max_results
        self.verbose = verbose
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.api_url = BRAVE_SEARCH_API_URL
        
        if self.verbose:
            logger.info("Initialized Brave Search client with direct HTTP requests")
    
    def search(self, query: str) -> List[SearchResult]:
        """
        Perform a search using Brave Search API with timeout handling and retries.
        
        Args:
            query: Search query string
            
        Returns:
            List of SearchResult objects
        """
        if self.verbose:
            logger.info(f"Searching Brave for: {query}")
        
        search_results = []
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # Flag to track if the search completed
                search_completed = False
                search_exception = None
                results = []
                
                # Define the search function to run in a separate thread
                def perform_search():
                    nonlocal search_completed, results, search_exception
                    try:
                        # Define headers and parameters for the request
                        headers = {
                            "Accept": "application/json",
                            "Accept-Encoding": "gzip",
                            "X-Subscription-Token": self.api_key
                        }
                        
                        params = {
                            "q": query,
                            "count": self.max_results
                        }
                        
                        # Make the HTTP request
                        response = requests.get(
                            self.api_url,
                            headers=headers,
                            params=params,
                            timeout=self.timeout
                        )
                        
                        # Check if the request was successful
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Extract results from response
                            if data and 'web' in data and 'results' in data['web']:
                                results = data['web']['results']
                                search_completed = True
                            else:
                                search_exception = Exception(f"No valid results returned from Brave Search. Response: {data}")
                        else:
                            search_exception = Exception(f"Brave Search API returned status code {response.status_code}: {response.text}")
                        
                        time.sleep(1.5) 
                    
                    except requests.exceptions.RequestException as e:
                        search_exception = e
                    except Exception as e:
                        search_exception = e
                
                # Create and start the search thread
                search_thread = threading.Thread(target=perform_search)
                search_thread.daemon = True  # Allow the thread to be terminated when the main thread exits
                search_thread.start()
                
                # Wait for the search to complete or timeout
                search_thread.join(timeout=self.timeout)
                
                # Check if search completed or timed out
                if not search_completed:
                    if search_thread.is_alive():
                        if self.verbose:
                            logger.warning(f"Search timed out after {self.timeout} seconds")
                        retry_count += 1
                        if retry_count <= self.max_retries:
                            if self.verbose:
                                logger.info(f"Retrying in {self.retry_delay} seconds (attempt {retry_count}/{self.max_retries})")
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            if self.verbose:
                                logger.error(f"Maximum retries reached for query: {query}")
                            return []
                    elif search_exception:
                        # Search thread completed but with an exception
                        raise search_exception
                
                # Process search results
                if self.verbose:
                    logger.info(f"Got {len(results)} results for query: {query}")
                
                # Convert to SearchResult objects
                for result in results:
                    search_results.append(SearchResult(
                        title=result.get('title', ''),
                        body=result.get('description', ''),
                        url=result.get('url', ''),
                        source=self._extract_domain(result.get('url', ''))
                    ))
                
                # Search successful, break the retry loop
                break
                
            except Exception as e:
                if self.verbose:
                    logger.error(f"Error during Brave search: {str(e)}")

                retry_count += 1
                if retry_count <= self.max_retries:
                    if self.verbose:
                        logger.info(f"Retrying in {self.retry_delay} seconds (attempt {retry_count}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    if self.verbose:
                        logger.error(f"Maximum retries reached for query: {query}")
                    return []
        
        return search_results
    
    def _extract_domain(self, url: str) -> str:
        """Extract the domain name from a URL."""
        pattern = r'https?://(?:www\.)?([^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return url