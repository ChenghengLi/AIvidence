"""DomainAnalyzer agent for analyzing website domains and content topics."""
import re
import json
import logging
from typing import Dict, Any
from urllib.parse import urlparse

from aividence.clients.model_client import ModelClient

logger = logging.getLogger("FactCheckTool.DomainAnalyzer")

class DomainAnalyzer:
    """
    Agent for analyzing website domains and determining their topics,
    required expertise, and verification strategies.
    """
    
    def __init__(self, model_client: ModelClient, verbose: bool = False):
        """
        Initialize the domain analyzer.
        
        Args:
            model_client: ModelClient instance for querying language models
            verbose: Whether to enable verbose logging
        """
        self.model_client = model_client
        self.verbose = verbose
        
    def analyze_domain(self, url: str, content: str) -> Dict[str, Any]:
        """
        Analyze the website domain and determine its topic, expertise required, and what to verify.
        
        Args:
            url: Website URL
            content: Website content
            
        Returns:
            Dictionary with domain analysis results
        """
        if self.verbose:
            logger.info(f"Analyzing domain for URL: {url}")
            
        # Extract domain from URL
        domain = self._extract_domain(url)
            
        system_prompt = """
        You are an expert in information analysis and fact-checking. Your task is to analyze a website's content 
        to determine its domain/topic and what types of claims would require verification.
        
        Consider:
        1. What is the main topic or domain of this website?
        2. What expertise would be needed to properly verify information in this domain?
        3. What are common misinformation patterns in this domain?
        4. What types of claims should be verified in this content?
        
        Format your response as a JSON object with the following structure:
        {
            "domain": "Domain name extracted from URL",
            "topic": "Main topic of the website",
            "domain_expertise_required": ["List", "of", "expertise", "fields"],
            "misinformation_patterns": ["Common", "patterns", "in", "this", "domain"],
            "verification_focus": ["Key", "areas", "to", "verify"],
            "red_flags": ["Potential", "indicators", "of", "misinformation"]
        }
        """
        
        # Create a content summary if it's too long
        content_summary = content
        if len(content) > 8000:
            content_summary = content[:4000] + "\n\n[...]\n\n" + content[-4000:]
        
        prompt = f"""
        Website URL: {url}
        
        Website content:
        {content_summary}
        
        Analyze this website to determine its domain/topic and what should be verified.
        Return your analysis in the required JSON format.
        """
        
        if self.verbose:
            logger.info("Sending domain analysis request to the model")
            
        response = self.model_client.run(prompt, system_prompt)
        
        if self.verbose:
            logger.info("Received domain analysis response")
            
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                
                # Ensure the domain is included
                if 'domain' not in analysis or not analysis['domain']:
                    analysis['domain'] = domain
                
                if self.verbose:
                    logger.info(f"Domain analysis complete. Topic: {analysis.get('topic', 'Unknown')}")
                
                return analysis
            else:
                if self.verbose:
                    logger.warning("Could not extract JSON from domain analysis response")
                
                # Create a default response
                return {
                    "domain": domain,
                    "topic": "Unknown",
                    "domain_expertise_required": ["General knowledge"],
                    "misinformation_patterns": ["Unverified claims"],
                    "verification_focus": ["Factual accuracy"],
                    "red_flags": ["Lack of sources"]
                }
        except Exception as e:
            if self.verbose:
                logger.error(f"Error processing domain analysis: {str(e)}")
            
            # Create a default response
            return {
                "domain": domain,
                "topic": "Unknown",
                "domain_expertise_required": ["General knowledge"],
                "misinformation_patterns": ["Unverified claims"],
                "verification_focus": ["Factual accuracy"],
                "red_flags": ["Lack of sources"]
            }
    
    def _extract_domain(self, url: str) -> str:
        """Extract the domain name from a URL."""
        pattern = r'https?://(?:www\.)?([^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return url