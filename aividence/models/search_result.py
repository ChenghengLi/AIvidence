"""SearchResult model for representing search results."""

class SearchResult:
    """
    Represents a search result from a web search.
    
    Attributes:
        title: Title of the search result
        body: Body text or description of the search result
        url: URL of the search result
        source: Source domain of the search result
    """
    def __init__(self, title: str, body: str, url: str, source: str):
        self.title = title
        self.body = body
        self.url = url
        self.source = source
    
    def __str__(self):
        return f"{self.title} - {self.source} ({self.url})"
    
    def __repr__(self):
        return f"SearchResult(title='{self.title}', source='{self.source}', url='{self.url}')"