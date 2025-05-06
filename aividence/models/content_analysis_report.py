"""ContentAnalysisReport model for representing the final analysis results."""
from typing import List, Dict
from pydantic import BaseModel, Field

from aividence.models.fact_claim import FactClaim
from aividence.models.fact_check_result import FactCheckResult

class ContentAnalysisReport(BaseModel):
    """
    The complete analysis report for a website or content source.
    
    Attributes:
        url: URL of the analyzed content
        domain: Domain name of the content source
        topic: Main topic of the content
        domain_expertise_required: List of expertise domains required to verify the content
        overall_score: Overall truthfulness score of the content (0-5)
        claims: List of factual claims extracted from the content
        verification_results: List of verification results for the claims
        summary: Summary of the analysis
        recommendations: List of recommendations for the reader
        analysis_date: Date when the analysis was performed
    """
    url: str
    domain: str
    topic: str
    domain_expertise_required: List[str]
    overall_score: float = Field(description="Overall truthfulness score from 0-5")
    claims: List[FactClaim] = []
    verification_results: List[FactCheckResult] = []
    summary: str = Field(description="Summary of the analysis")
    recommendations: List[str] = Field(description="Recommendations for the reader")
    analysis_date: str = Field(description="Date when the analysis was performed")
    
    def to_markdown_report(self) -> str:
        """Generate a markdown report from the analysis results."""
        report = f"# Misinformation Analysis Report\n\n"
        report += f"## Website: [{self.domain}]({self.url})\n\n"
        report += f"**Topic:** {self.topic}\n\n"
        report += f"**Overall Truthfulness Score:** {self.overall_score}/5\n\n"
        report += f"**Analysis Date:** {self.analysis_date}\n\n"
        
        # Add recency warning if needed
        recent_claims = [r for r in self.verification_results if r.is_recent_news]
        if recent_claims:
            report += "⚠️ **RECENCY WARNING** ⚠️\n\n"
            report += "_This analysis contains claims about very recent events. Information available online may be limited or still evolving. "
            report += "Results should be interpreted with caution and reevaluated as more information becomes available._\n\n"
            report += "---\n\n"
        
        report += "## Summary\n\n"
        report += f"{self.summary}\n\n"
        
        # Sort verification results by score
        sorted_results = sorted(self.verification_results, key=lambda x: x.score)
        
        # Most concerning claims (lowest scores)
        if sorted_results:
            report += "## Most Concerning Claims\n\n"
            for result in sorted_results[:3]:  # Top 3 most concerning
                report += f"### Claim: {result.claim}\n\n"
                report += f"**Truthfulness Score:** {result.score}/5\n\n"
                report += f"**Explanation:** {result.explanation}\n\n"
                if result.contradictions:
                    report += "**Contradicting Evidence:**\n\n"
                    for contradiction in result.contradictions:
                        report += f"- {contradiction}\n"
                    report += "\n"
                
                # Add search verification details
                report += "**Search Verification:**\n\n"
                report += f"*Search Queries:* {', '.join(result.search_queries)}\n\n"
                report += "**Sources:**\n\n"
                for source in result.sources[:5]:  # Limit to 5 sources
                    report += f"- [{source.get('title', 'Source')}]({source.get('url', '#')})\n"
                report += "\n"
            
            # Most accurate claims (highest scores)
            report += "## Most Accurate Claims\n\n"
            for result in reversed(sorted_results[-3:]):  # Top 3 most accurate
                report += f"### Claim: {result.claim}\n\n"
                report += f"**Truthfulness Score:** {result.score}/5\n\n"
                report += f"**Explanation:** {result.explanation}\n\n"
                if result.evidence:
                    report += "**Supporting Evidence:**\n\n"
                    for evidence in result.evidence[:3]:  # Limit to 3 pieces of evidence
                        report += f"- {evidence}\n"
                    report += "\n"
                
                # Add search verification details
                report += "**Search Verification:**\n\n"
                report += f"*Search Queries:* {', '.join(result.search_queries)}\n\n"
                report += "**Sources:**\n\n"
                for source in result.sources[:5]:  # Limit to 5 sources
                    report += f"- [{source.get('title', 'Source')}]({source.get('url', '#')})\n"
                report += "\n"
        
        # All claims with verification details
        report += "## All Claims Verification Details\n\n"
        for i, result in enumerate(self.verification_results, 1):
            report += f"### {i}. {result.claim}\n\n"
            report += f"**Truthfulness Score:** {result.score}/5 (Confidence: {result.confidence:.2f})\n\n"
            report += f"**Explanation:** {result.explanation}\n\n"
            
            # Evidence sections
            if result.evidence:
                report += "**Supporting Evidence:**\n\n"
                for evidence in result.evidence:
                    report += f"- {evidence}\n"
                report += "\n"
            
            if result.contradictions:
                report += "**Contradicting Evidence:**\n\n"
                for contradiction in result.contradictions:
                    report += f"- {contradiction}\n"
                report += "\n"
            
            # Search details
            report += "**Search Verification:**\n\n"
            report += f"*Search Queries:*\n\n"
            for query in result.search_queries:
                report += f"- {query}\n"
            report += "\n"
            
            report += "**Sources:**\n\n"
            for source in result.sources:
                report += f"- [{source.get('title', 'Source')}]({source.get('url', '#')})\n"
            report += "\n"
        
        report += "## Recommendations for Readers\n\n"
        for recommendation in self.recommendations:
            report += f"- {recommendation}\n"
        
        return report