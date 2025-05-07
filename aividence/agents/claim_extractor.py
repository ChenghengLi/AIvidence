"""ClaimExtractor agent for extracting verifiable claims from content."""
import re
import json
import logging
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from aividence.clients.model_client import ModelClient
from aividence.models.fact_claim import FactClaim

logger = logging.getLogger("FactCheckTool.ClaimExtractor")

class ClaimExtractor:
    """
    Agent for extracting verifiable factual claims from website content.
    """
    
    def __init__(self, model_client: ModelClient, verbose: bool = False):
        """
        Initialize the claim extractor.
        
        Args:
            model_client: ModelClient instance for querying language models
            verbose: Whether to enable verbose logging
        """
        self.model_client = model_client
        self.verbose = verbose
        
    def extract_claims(self, content: str, domain_analysis: Dict[str, Any], max_claims: int = 10) -> List[FactClaim]:
        """
        Extract verifiable claims from the website content.
        
        Args:
            content: Website content
            domain_analysis: Results from domain analysis
            max_claims: Maximum number of claims to extract
            
        Returns:
            List of FactClaim objects
        """
        if self.verbose:
            logger.info(f"Extracting claims from content of length {len(content)} characters")
            
        # Split content into chunks if it's too long
        chunks = self._split_content(content)
        
        all_claims = []
        
        for i, chunk in enumerate(chunks):
            if self.verbose:
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
            chunk_claims = self._extract_claims_from_chunk(chunk, domain_analysis, i)
            all_claims.extend(chunk_claims)
            
            # Stop if we have enough claims
            if len(all_claims) >= max_claims:
                all_claims = all_claims[:max_claims]
                break
                
        # Remove duplicates
        seen_claims = set()
        unique_claims = []
        
        for claim in all_claims:
            claim_text = claim.claim.lower()
            if claim_text not in seen_claims:
                seen_claims.add(claim_text)
                unique_claims.append(claim)
        
        if self.verbose:
            logger.info(f"Extracted {len(unique_claims)} unique claims")
            
        return unique_claims
    
    def _split_content(self, content: str) -> List[str]:
        """Split content into manageable chunks."""
        if len(content) <= 30000:
            return [content]
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=30000,
            chunk_overlap=1000,
            length_function=len,
        )
        
        chunks = text_splitter.split_text(content)
        
        if self.verbose:
            logger.info(f"Split content into {len(chunks)} chunks")
            
        return chunks
    
    def _extract_claims_from_chunk(self, content_chunk: str, domain_analysis: Dict[str, Any], chunk_id: int) -> List[FactClaim]:
        """Extract claims from a single content chunk."""
        system_prompt = """
        You are an expert in fact-checking and misinformation detection. Your task is to identify specific, verifiable claims 
        from a piece of web content, GIVE ME ONLY THE 5 MOST RELEVANT CLAIMS TO CHECK, focusing on statements that:
        
        1. Make factual assertions that can be verified or disproven
        2. Are specific rather than vague
        3. Are meaningful and consequential to the topic
        4. Might contain misinformation based on the domain analysis provided
        
        For each claim, identify:
        - The specific claim text
        - Keywords that would be useful for verification
        - Its importance on a scale of 1-10
        
        Format your response as a JSON array of objects with this structure:
        [
            {
                "claim": "The specific claim statement",
                "topic": "Specific subtopic of the claim",
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "importance": 8
            },
            ...
        ]
        
        Focus on the most important and potentially problematic claims. Include both:
        - Claims that seem questionable or might be misinformation
        - Important factual claims that should be verified even if they seem correct
        """
        
        topic = domain_analysis.get("topic", "Unknown")
        verification_focus = domain_analysis.get("verification_focus", ["Factual accuracy"])
        red_flags = domain_analysis.get("red_flags", ["Lack of sources"])
        
        prompt = f"""
        CONTENT CHUNK:
        {content_chunk}
        
        DOMAIN ANALYSIS:
        Topic: {topic}
        Verification Focus: {', '.join(verification_focus)}
        Red Flags: {', '.join(red_flags)}
        
        Extract specific, verifiable claims from this content chunk, 
        prioritizing those that align with the verification focus and potential red flags.
        
        Return the claims in the required JSON array format.
        """
        
        if self.verbose:
            logger.info(f"Sending claim extraction request for chunk {chunk_id}")
            
        response = self.model_client.run(prompt, system_prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                claims_data = json.loads(json_match.group(0))
                
                # Convert to FactClaim objects
                claims = []
                for i, claim_data in enumerate(claims_data):
                    claim_id = f"claim_{chunk_id}_{i+1}"
                    claims.append(FactClaim(
                        id=claim_id,
                        claim=claim_data.get("claim", ""),
                        topic=claim_data.get("topic", topic),
                        keywords=claim_data.get("keywords", []),
                        importance=claim_data.get("importance", 5)
                    ))
                
                return claims
            else:
                if self.verbose:
                    logger.warning(f"Could not extract JSON from claim extraction response for chunk {chunk_id}")
                return []
        except Exception as e:
            if self.verbose:
                logger.error(f"Error processing claim extraction for chunk {chunk_id}: {str(e)}")
            return []
