"""
Internet Research Tool - Web search with per-session caching.

Wraps the WebSearcher to provide debate-focused research with
DuckDuckGo search, caching results per session to avoid redundant API calls.
"""

import hashlib
from typing import Optional
from dataclasses import dataclass, field
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.web_search import WebSearcher, SearchResult


class InternetResearchInput(BaseModel):
    """Input schema for internet research."""
    topic: str = Field(..., description="The topic to research")
    search_type: str = Field(
        default="debate",
        description="Type of search: 'debate' (pro/con/facts), 'general', or 'experts'"
    )


@dataclass
class SessionCache:
    """Per-session cache for search results."""
    results: dict = field(default_factory=dict)
    
    def get_key(self, topic: str, search_type: str) -> str:
        """Generate cache key from topic and search type."""
        content = f"{topic.lower().strip()}:{search_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, topic: str, search_type: str) -> Optional[dict]:
        """Get cached results if available."""
        key = self.get_key(topic, search_type)
        return self.results.get(key)
    
    def set(self, topic: str, search_type: str, data: dict):
        """Cache results."""
        key = self.get_key(topic, search_type)
        self.results[key] = data
    
    def clear(self):
        """Clear all cached results."""
        self.results.clear()


class InternetResearchTool(BaseTool):
    """
    CrewAI tool for internet research with session-based caching.
    
    Features:
    - DuckDuckGo-based web search (no API key required)
    - Debate-focused search (pro/con/facts)
    - Per-session caching to avoid redundant searches
    - Toggle to enable/disable internet access
    """
    
    name: str = "Internet Research"
    description: str = (
        "Search the internet for information about a topic. "
        "Can search for debate arguments (pro/con), general facts, or experts. "
        "Returns structured results with sources."
    )
    args_schema: type[BaseModel] = InternetResearchInput
    
    # Instance attributes
    use_internet: bool = True
    _cache: SessionCache = None
    _searcher: WebSearcher = None
    
    def __init__(self, use_internet: bool = True, **kwargs):
        """
        Initialize the research tool.
        
        Args:
            use_internet: Whether to actually perform web searches
        """
        super().__init__(**kwargs)
        self.use_internet = use_internet
        self._cache = SessionCache()
        self._searcher = WebSearcher()
    
    def _run(self, topic: str, search_type: str = "debate") -> str:
        """
        Execute internet research.
        
        Args:
            topic: The topic to research
            search_type: Type of search ('debate', 'general', 'experts')
            
        Returns:
            Formatted string with research results
        """
        if not self.use_internet:
            return self._no_internet_response(topic)
        
        # Check cache first
        cached = self._cache.get(topic, search_type)
        if cached:
            return self._format_results(cached, from_cache=True)
        
        # Perform search
        try:
            if search_type == "debate":
                results = self._search_debate(topic)
            elif search_type == "experts":
                results = self._search_experts(topic)
            else:
                results = self._search_general(topic)
            
            # Cache results
            self._cache.set(topic, search_type, results)
            
            return self._format_results(results, from_cache=False)
            
        except Exception as e:
            return f"Research failed: {str(e)}. Proceeding without internet data."
    
    def _search_debate(self, topic: str) -> dict:
        """Search for debate-focused content (pro/con/facts)."""
        results = self._searcher.search_debate_topic(topic)
        
        return {
            "type": "debate",
            "topic": topic,
            "pro_arguments": [self._result_to_dict(r) for r in results.get("pro", [])],
            "con_arguments": [self._result_to_dict(r) for r in results.get("con", [])],
            "facts": [self._result_to_dict(r) for r in results.get("facts", [])],
        }
    
    def _search_general(self, topic: str) -> dict:
        """Search for general information."""
        results = self._searcher.search(f"{topic} overview facts", max_results=5)
        
        return {
            "type": "general",
            "topic": topic,
            "results": [self._result_to_dict(r) for r in results],
        }
    
    def _search_experts(self, topic: str) -> dict:
        """Search for experts and notable figures on the topic."""
        queries = [
            f"experts on {topic}",
            f"notable people {topic}",
            f"{topic} thought leaders academics",
        ]
        
        all_results = []
        for query in queries:
            results = self._searcher.search(query, max_results=3)
            all_results.extend(results)
        
        return {
            "type": "experts",
            "topic": topic,
            "results": [self._result_to_dict(r) for r in all_results],
        }
    
    def _result_to_dict(self, result: SearchResult) -> dict:
        """Convert SearchResult to dict."""
        return {
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
            "content": result.content[:500] if result.content else "",
        }
    
    def _format_results(self, results: dict, from_cache: bool) -> str:
        """Format results as a readable string."""
        cache_note = " (cached)" if from_cache else ""
        lines = [f"## Research Results{cache_note}: {results['topic']}\n"]
        
        if results["type"] == "debate":
            lines.append("### Pro Arguments")
            for i, r in enumerate(results["pro_arguments"][:3], 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   {r['snippet']}")
                lines.append(f"   Source: {r['url']}\n")
            
            lines.append("### Con Arguments")
            for i, r in enumerate(results["con_arguments"][:3], 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   {r['snippet']}")
                lines.append(f"   Source: {r['url']}\n")
            
            lines.append("### Key Facts")
            for i, r in enumerate(results["facts"][:3], 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   {r['snippet']}")
                lines.append(f"   Source: {r['url']}\n")
        
        elif results["type"] == "experts":
            lines.append("### Experts and Notable Figures")
            for i, r in enumerate(results["results"][:5], 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   {r['snippet']}")
                lines.append(f"   Source: {r['url']}\n")
        
        else:  # general
            lines.append("### General Information")
            for i, r in enumerate(results["results"][:5], 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   {r['snippet']}")
                lines.append(f"   Source: {r['url']}\n")
        
        return "\n".join(lines)
    
    def _no_internet_response(self, topic: str) -> str:
        """Response when internet is disabled."""
        return (
            f"Internet research is disabled for this session.\n"
            f"Topic '{topic}' will be debated using only the model's knowledge "
            f"and any pre-loaded domain adapters."
        )
    
    def clear_cache(self):
        """Clear the session cache."""
        self._cache.clear()
    
    def enable_internet(self):
        """Enable internet research."""
        self.use_internet = True
    
    def disable_internet(self):
        """Disable internet research."""
        self.use_internet = False
