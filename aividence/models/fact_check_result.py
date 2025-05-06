"""FactCheckResult model for representing verification results."""
from typing import List, Dict
from pydantic import BaseModel, Field

class FactCheckResult(BaseModel):
    """
    Represents the result of verifying a factual claim.
    
    Attributes:
        claim_id: ID of the claim being verified
        claim: The claim text
        score: Truthfulness score (0-5, where 0 is completely false and 5 is completely true)
        confidence: Confidence in the verification (0-1)
        evidence: List of evidence supporting the verification
        contradictions: List of evidence contradicting the claim
        sources: List of sources used for verification
        search_queries: List of search queries used for verification
        explanation: Explanation of the verification result
        is_recent_news: Flag indicating if the claim is about very recent events
    """
    claim_id: str
    claim: str
    score: float = Field(description="Truthfulness score from 0-5, where 0 is completely false and 5 is completely true")
    confidence: float = Field(description="Confidence in the verification from 0-1")
    evidence: List[str] = Field(description="Evidence supporting the verification result")
    contradictions: List[str] = Field(description="Evidence contradicting the claim")
    sources: List[Dict[str, str]] = Field(description="Sources used for verification with title and URL")
    search_queries: List[str] = Field(description="Search queries used for verification")
    explanation: str = Field(description="Explanation of the verification result")
    is_recent_news: bool = Field(default=False, description="Flag indicating if the claim is about very recent events")