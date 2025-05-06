"""ClaimVerifier agent for verifying factual claims using web search."""
import re
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from aividence.clients.model_client import ModelClient
from aividence.clients.web_search_client import WebSearchClient
from aividence.models.fact_claim import FactClaim
from aividence.models.search_result import SearchResult
from aividence.models.fact_check_result import FactCheckResult

logger = logging.getLogger("FactCheckTool.ClaimVerifier")

class ClaimVerifier:
    """
    Agent for verifying factual claims by searching for evidence and analyzing results.
    """
    
    def __init__(self, model_client: ModelClient, search_client: WebSearchClient, verbose: bool = False):
        """
        Initialize the claim verifier.
        
        Args:
            model_client: ModelClient instance for querying language models
            search_client: WebSearchClient instance for searching the web
            verbose: Whether to enable verbose logging
        """
        self.model_client = model_client
        self.search_client = search_client
        self.verbose = verbose
        
    def verify_claim(self, claim: FactClaim, domain_analysis: Dict[str, Any]) -> FactCheckResult:
        """
        Verify a single claim by searching for evidence and analyzing results.
        
        Args:
            claim: The claim to verify
            domain_analysis: Domain analysis results for context
            
        Returns:
            FactCheckResult with the verification details
        """
        if self.verbose:
            logger.info(f"Verifying claim: {claim.claim}")
            
        # Step 1: Formulate search queries based on the claim and keywords
        search_queries = self._formulate_search_queries(claim)
        
        # Step 2: Run searches
        all_search_results = []
        search_sources = []
        
        for query in search_queries:
            if self.verbose:
                logger.info(f"Searching for: {query}")
                
            try:
                results = self.search_client.search(query)
                
                # Add to combined results
                all_search_results.extend(results)
                
                # Add sources
                for result in results:
                    search_sources.append({
                        "title": result.title,
                        "url": result.url,
                        "source": result.source
                    })
                    
            except Exception as e:
                if self.verbose:
                    logger.error(f"Error during search for query '{query}': {str(e)}")
        
        # Step 3: Format search results for analysis
        formatted_results = self._format_search_results(all_search_results, search_queries)
        
        # Step 4: Analyze search results to verify the claim
        verification_result = self._analyze_search_results(claim, formatted_results, search_sources, search_queries, domain_analysis)
        
        if self.verbose:
            logger.info(f"Verification complete. Score: {verification_result.score}/5")
            
        return verification_result
    
    def _formulate_search_queries(self, claim: FactClaim) -> List[str]:
        """Generate search queries for claim verification."""
        system_prompt = """
        You are a fact-checking expert. Your task is to formulate effective search queries to verify a specific claim.
        
        Create 1-2 search queries that:
        1. Focus on the key factual elements of the claim
        2. Use different phrasings and keywords to get diverse results
        3. Include queries designed to find both supporting and contradicting evidence
        4. Are specific enough to get relevant results
        
        Return only the search queries, one per line. No explanations or other text.
        """
        
        prompt = f"""
        CLAIM: {claim.claim}
        
        TOPIC: {claim.topic}
        
        KEYWORDS: {', '.join(claim.keywords)}
        
        Formulate 1-2 effective search queries to verify this claim.
        """
        
        if self.verbose:
            logger.info("Formulating search queries")
            
        response = self.model_client.run(prompt, system_prompt)
        
        # Extract queries from response
        queries = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Limit to 5 queries
        queries = queries[:5]
        
        if self.verbose:
            logger.info(f"Generated {len(queries)} search queries")
            
        return queries
    
    def _format_search_results(self, search_results: List[SearchResult], search_queries: List[str]) -> str:
        """Format search results for analysis."""
        formatted_results = ""
        
        # Group results by search query
        query_results = {query: [] for query in search_queries}
        
        # Add all results
        for result in search_results:
            formatted_results += f"TITLE: {result.title}\n"
            formatted_results += f"SOURCE: {result.source}\n"
            formatted_results += f"URL: {result.url}\n"
            formatted_results += f"CONTENT: {result.body}\n\n"
        
        # Truncate if too long
        if len(formatted_results) > 6000:
            formatted_results = formatted_results[:6000] + "\n...[truncated]..."
            
        return formatted_results
    
    def _analyze_search_results(self, claim: FactClaim, formatted_results: str, 
                               sources: List[Dict[str, str]], search_queries: List[str],
                               domain_analysis: Dict[str, Any]) -> FactCheckResult:
        """Analyze search results to determine the veracity of the claim."""
        if self.verbose:
            logger.info("Analyzing search results")
            
        system_prompt = """
        You are an expert fact-checker evaluating the veracity of a claim based on search results. 
        Carefully analyze the evidence and determine how well the claim is supported or contradicted.
        
        Provide your analysis in JSON format with this structure:
        {
            "score": 0-5 (0 = completely false, 5 = completely true),
            "confidence": 0-1 (your confidence in this assessment),
            "evidence": ["List", "of", "supporting", "evidence"],
            "contradictions": ["List", "of", "contradicting", "evidence"],
            "recency_factor": true/false (whether this is very recent news that might have limited coverage),
            "explanation": "Detailed explanation of your reasoning"
        }
        
        Consider:
        - The reliability of sources (peer-reviewed journals, recognized authorities, etc.)
        - The consistency of evidence across different sources
        - The specificity and relevance of the information
        - Any contradictions between sources
        - The overall weight of evidence
        - Recency of the information - for very recent news (past few days/weeks), there might be limited information
          available online and evaluations should acknowledge this with appropriate caution
        - Publication dates of sources - note if the claim involves very recent events that might not have been
          thoroughly verified by multiple sources yet
        
        If the claim involves recent events (past few days/weeks) that might not have extensive coverage yet,
        explicitly acknowledge this in your explanation and adjust your confidence level accordingly.
        """
        
        domain_expertise = domain_analysis.get("domain_expertise_required", ["General knowledge"])
        misinformation_patterns = domain_analysis.get("misinformation_patterns", ["Unverified claims"])
        
        # Get current date to check recency
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""
        CLAIM TO VERIFY: {claim.claim}
        
        TOPIC: {claim.topic}
        
        DOMAIN EXPERTISE REQUIRED: {', '.join(domain_expertise)}
        
        COMMON MISINFORMATION PATTERNS: {', '.join(misinformation_patterns)}
        
        CURRENT DATE: {current_date}
        
        SEARCH RESULTS:
        {formatted_results}
        
        Analyze these search results to determine the veracity of the claim.
        Pay special attention to publication dates and whether this is very recent news, which might mean
        limited information is available online. If the claim relates to very recent events, be explicit 
        about the limitations in verification and adjust your confidence accordingly.
        
        Return your analysis in the required JSON format.
        """
        
        if self.verbose:
            logger.info("Sending verification analysis request to the model")
            
        response = self.model_client.run(prompt, system_prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                
                # Check if this is recent news
                is_recent_news = analysis.get("recency_factor", False)
                
                # Adjust explanation for recent news
                explanation = analysis.get("explanation", "No explanation provided")
                if is_recent_news and "recent" not in explanation.lower():
                    explanation += "\n\nNote: This claim involves recent events, and information available online may be limited or still evolving. Verification is preliminary and should be revisited as more information becomes available."
                
                # Adjust confidence for recent news
                confidence = analysis.get("confidence", 0.5)
                if is_recent_news and confidence > 0.7:
                    confidence = 0.7  # Cap confidence for very recent news
                
                # Clean up and deduplicate sources
                unique_sources = []
                seen_urls = set()
                
                for source in sources:
                    url = source.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_sources.append({
                            "title": source.get("title", "Source"),
                            "url": url
                        })
                
                # Create verification result
                result = FactCheckResult(
                    claim_id=claim.id,
                    claim=claim.claim,
                    score=analysis.get("score", 0),
                    confidence=confidence,
                    evidence=analysis.get("evidence", []),
                    contradictions=analysis.get("contradictions", []),
                    sources=unique_sources,
                    search_queries=search_queries,
                    explanation=explanation,
                    is_recent_news=is_recent_news
                )
                
                return result
            else:
                if self.verbose:
                    logger.warning("Could not extract JSON from verification analysis response")
                
                # Create a default result
                return FactCheckResult(
                    claim_id=claim.id,
                    claim=claim.claim,
                    score=2.5,  # Neutral score
                    confidence=0.3,
                    evidence=[],
                    contradictions=[],
                    sources=[{"title": "No sources found", "url": "#"}],
                    search_queries=search_queries,
                    explanation="Analysis failed to provide a clear determination."
                )
        except Exception as e:
            if self.verbose:
                logger.error(f"Error processing verification analysis: {str(e)}")
            
            # Create a default result
            return FactCheckResult(
                claim_id=claim.id,
                claim=claim.claim,
                score=2.5,  # Neutral score
                confidence=0.3,
                evidence=[],
                contradictions=[],
                sources=[{"title": "No sources found", "url": "#"}],
                search_queries=search_queries,
                explanation="Analysis failed due to an error."
            )