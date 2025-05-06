"""FactClaim model for representing claims to be verified."""
from typing import List
from pydantic import BaseModel, Field

class FactClaim(BaseModel):
    """
    A factual claim extracted from content that needs verification.
    
    Attributes:
        id: Unique identifier for the claim
        claim: The actual claim text
        topic: Topic category of the claim
        keywords: List of keywords relevant to the claim
        importance: Importance score of the claim (1-10)
    """
    id: str
    claim: str
    topic: str
    keywords: List[str]
    importance: int = Field(description="Importance of this claim on a scale of 1-10")