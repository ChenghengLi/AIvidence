"""FactCheckEngine for analyzing content and checking its factual accuracy."""
import os
import re
import json  
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from aividence.config import (
    DEFAULT_MODEL_NAME, 
    BRAVE_API_KEY, 
    DEFAULT_MAX_CLAIMS
)
from aividence.clients.content_scraper import ContentScraper
from aividence.clients.model_client import ModelClient
from aividence.clients.web_search_client import WebSearchClient
from aividence.agents.domain_analyzer import DomainAnalyzer
from aividence.agents.claim_extractor import ClaimExtractor
from aividence.agents.claim_verifier import ClaimVerifier
from aividence.models.fact_claim import FactClaim
from aividence.models.fact_check_result import FactCheckResult
from aividence.models.content_analysis_report import ContentAnalysisReport

logger = logging.getLogger("FactCheckTool.FactCheckEngine")

class FactCheckEngine:
    """
    Main engine for analyzing content and checking its factual accuracy.
    Orchestrates the full pipeline from content retrieval to final report generation.
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, 
                 api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, 
                 verbose: bool = False, 
                 brave_api_key: str = BRAVE_API_KEY):
        """
        Initialize the fact check engine.
        
        Args:
            model_name: Name of the LLM to use
            api_key: API key for the language model
            base_url: Base URL for the language model (for Ollama models)
            verbose: Whether to enable verbose logging
            brave_api_key: API key for Brave Search
        """
        self.verbose = verbose
        
        if self.verbose:
            logger.info(f"Initializing FactCheckEngine with model: {model_name}")
            
        self.model_client = ModelClient(model_name, api_key, base_url, verbose=self.verbose)
        
        # Initialize search tool with Brave Search
        self.search_client = WebSearchClient(api_key=brave_api_key, verbose=self.verbose)
        
        # Initialize website content loader
        self.content_scraper = ContentScraper(verbose=self.verbose)
        
        # Initialize agents
        self.domain_analyzer = DomainAnalyzer(self.model_client, verbose=self.verbose)
        self.claim_extractor = ClaimExtractor(self.model_client, verbose=self.verbose)
        self.claim_verifier = ClaimVerifier(self.model_client, self.search_client, verbose=self.verbose)

    def analyze_content(self, source: str, source_type: Optional[str] = None, max_claims: int = DEFAULT_MAX_CLAIMS) -> ContentAnalysisReport:
        """
        Analyze content from a URL or HTML file for misinformation.
        
        Args:
            source: Source of content (URL or file path)
            source_type: Type of source ('url' or 'file'). If None, type is auto-detected.
            max_claims: Maximum number of claims to verify
            
        Returns:
            ContentAnalysisReport with analysis details
        """
        if self.verbose:
            logger.info(f"Starting analysis of content from: {source}")
            
        # Step 1: Load content
        content = self._load_content(source, source_type)
        
        # For file sources, we need a URL-like identifier for the domain analysis
        url = source
        if source_type == 'file' or (source_type is None and os.path.isfile(source)):
            # Use a pseudo-URL based on the filename
            filename = os.path.basename(source)
            url = f"file://{filename}"
        
        # Step 2: Analyze domain and topic
        domain_analysis = self.domain_analyzer.analyze_domain(url, content)
        
        # Step 3: Extract claims to verify
        claims = self.claim_extractor.extract_claims(content, domain_analysis, max_claims)
        
        # Sort claims by importance
        claims = sorted(claims, key=lambda x: x.importance, reverse=True)[:max_claims]
        
        # Step 4: Verify each claim
        verification_results = []
        for claim in claims:
            if self.verbose:
                logger.info(f"Verifying claim {claim.id}: {claim.claim}")
                
            result = self.claim_verifier.verify_claim(claim, domain_analysis)
            verification_results.append(result)
        
        # Step 5: Generate overall analysis
        analysis_result = self._generate_overall_analysis(url, domain_analysis, claims, verification_results)
        
        if self.verbose:
            logger.info(f"Content analysis complete. Overall score: {analysis_result.overall_score}/5")
            
        return analysis_result
    
    def _load_content(self, source: str, source_type: Optional[str] = None) -> str:
        """
        Load content from a source (URL or HTML file).
        
        Args:
            source: Source of content (URL or file path)
            source_type: Type of source ('url' or 'file'). If None, type is auto-detected.
            
        Returns:
            str: The content as text
            
        Raises:
            ValueError: If the content could not be loaded
        """
        if self.verbose:
            logger.info(f"Loading content from source: {source}")
        
        try:
            # Use the content scraper
            content = self.content_scraper.load_content(source, source_type)
            
            if self.verbose:
                logger.info(f"Successfully loaded {len(content)} characters from source")
                
            return content
        except Exception as e:
            if self.verbose:
                logger.error(f"Error loading content: {str(e)}")
            raise ValueError(f"Could not load content from source: {source}")
    
    # Maintain backward compatibility
    def analyze_website(self, url: str, max_claims: int = DEFAULT_MAX_CLAIMS) -> ContentAnalysisReport:
        """
        Legacy method to maintain backward compatibility.
        
        Args:
            url: Website URL to analyze
            max_claims: Maximum number of claims to verify
            
        Returns:
            ContentAnalysisReport with analysis details
        """
        return self.analyze_content(url, source_type='url', max_claims=max_claims)
    
    def _generate_overall_analysis(self, url: str, domain_analysis: Dict[str, Any], 
                                 claims: List[FactClaim], verification_results: List[FactCheckResult]) -> ContentAnalysisReport:
        """Generate overall analysis of the website."""
        if self.verbose:
            logger.info("Generating overall analysis")
            
        # Calculate overall score (weighted by importance)
        total_weight = sum(claim.importance for claim in claims)
        total_score = 0
        
        for claim in claims:
            # Find corresponding verification result
            for result in verification_results:
                if result.claim_id == claim.id:
                    # Weight by importance
                    total_score += result.score * claim.importance
                    break
        
        overall_score = 2.5  # Default neutral score
        if total_weight > 0:
            overall_score = round(total_score / total_weight, 1)
        
        domain = domain_analysis.get("domain", "unknown")
        topic = domain_analysis.get("topic", "Unknown")
        domain_expertise = domain_analysis.get("domain_expertise_required", ["General knowledge"])
        
        # Generate summary and recommendations
        summary = self._generate_summary(domain_analysis, verification_results, overall_score)
        recommendations = self._generate_recommendations(domain_analysis, verification_results, overall_score)
        
        # Get current date for the report
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create result object
        result = ContentAnalysisReport(
            url=url,
            domain=domain,
            topic=topic,
            domain_expertise_required=domain_expertise,
            overall_score=overall_score,
            claims=claims,
            verification_results=verification_results,
            summary=summary,
            recommendations=recommendations,
            analysis_date=current_date
        )
        
        return result
    
    def _generate_summary(self, domain_analysis: Dict[str, Any], verification_results: List[FactCheckResult], overall_score: float) -> str:
        """Generate a summary of the analysis."""
        system_prompt = """
        You are a misinformation analysis expert. Create a concise summary of the website analysis
        based on the verification results and domain analysis.
        
        Your summary should:
        1. Highlight the overall trustworthiness of the website
        2. Note major patterns of accurate or inaccurate information
        3. Identify specific areas of concern if any
        4. Be objective and evidence-based
        5. Be approximately 150-250 words
        """
        
        # Prepare verification results for the summary
        formatted_results = []
        for result in verification_results:
            formatted_results.append({
                "claim": result.claim,
                "score": result.score,
                "explanation": result.explanation
            })
        
        topic = domain_analysis.get("topic", "Unknown")
        misinformation_patterns = domain_analysis.get("misinformation_patterns", ["Unverified claims"])
        
        prompt = f"""
        DOMAIN TOPIC: {topic}
        
        OVERALL SCORE: {overall_score}/5
        
        COMMON MISINFORMATION PATTERNS: {', '.join(misinformation_patterns)}
        
        VERIFICATION RESULTS:
        {json.dumps(formatted_results, indent=2)}
        
        Generate a concise summary of this website's information quality and trustworthiness.
        """
        
        if self.verbose:
            logger.info("Generating analysis summary")
            
        response = self.model_client.run(prompt, system_prompt)
        return response
    
    def _generate_recommendations(self, domain_analysis: Dict[str, Any], verification_results: List[FactCheckResult], overall_score: float) -> List[str]:
        """Generate recommendations for readers."""
        system_prompt = """
        You are a media literacy expert. Provide practical recommendations for readers
        about how to approach this website's information based on the analysis results.
        
        Your recommendations should:
        1. Be actionable and specific
        2. Help readers critically evaluate the information
        3. Suggest additional sources or verification methods if needed
        4. Be proportionate to the severity of misinformation found
        
        Return a list of 3-5 recommendations, each as a complete sentence.
        Format as a plain list, one recommendation per line.
        """
        
        red_flags = domain_analysis.get("red_flags", ["Lack of sources"])
        
        # Count verification results by score range
        high_scores = len([r for r in verification_results if r.score >= 4])
        mid_scores = len([r for r in verification_results if 2 <= r.score < 4])
        low_scores = len([r for r in verification_results if r.score < 2])
        
        prompt = f"""
        WEBSITE OVERALL SCORE: {overall_score}/5
        
        RED FLAGS IDENTIFIED: {', '.join(red_flags)}
        
        VERIFICATION RESULTS SUMMARY:
        - Claims with high trustworthiness (4-5): {high_scores}
        - Claims with moderate trustworthiness (2-3): {mid_scores}
        - Claims with low trustworthiness (0-1): {low_scores}
        
        Provide 3-5 practical recommendations for readers about how to approach information on this website.
        """
        
        if self.verbose:
            logger.info("Generating reader recommendations")
            
        response = self.model_client.run(prompt, system_prompt)
        
        # Parse recommendations into a list
        recommendations = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Clean up bullet points if present
        recommendations = [re.sub(r'^[-*•]?\s*', '', rec) for rec in recommendations]
        
        return recommendations