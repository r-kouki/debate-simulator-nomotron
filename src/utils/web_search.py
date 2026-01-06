"""
Web search utilities for the debate simulator.

Provides real-time web search and content extraction for any debate topic.
"""

import re
import asyncio
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


@dataclass
class SearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    content: str = ""  # Full extracted content


@dataclass
class ResearchData:
    """Collected research data for a debate topic."""
    topic: str
    pro_arguments: list[str]
    con_arguments: list[str]
    facts: list[str]
    sources: list[str]


class WebSearcher:
    """
    Web search and content extraction for debate research.
    
    Uses DuckDuckGo for search (free, no API key needed) and
    httpx + BeautifulSoup for content extraction.
    """
    
    def __init__(self, timeout: float = 10.0, max_results: int = 5):
        self.timeout = timeout
        self.max_results = max_results
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._client
    
    def search_sync(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Synchronous web search using DuckDuckGo.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        results = []
        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=num_results))
                
            for r in search_results:
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", r.get("link", "")),
                    snippet=r.get("body", r.get("snippet", "")),
                ))
        except Exception as e:
            print(f"[WebSearcher] Search error: {e}")
        
        return results
    
    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Async web search using DuckDuckGo.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        # DuckDuckGo search is sync, run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.search_sync(query, num_results)
        )
    
    def _extract_text(self, html: str, max_length: int = 2000) -> str:
        """Extract readable text from HTML content."""
        soup = BeautifulSoup(html, "lxml")
        
        # Remove script, style, nav elements
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        
        # Get text from paragraphs (most relevant content)
        paragraphs = soup.find_all("p")
        text_parts = []
        total_length = 0
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:  # Skip very short paragraphs
                text_parts.append(text)
                total_length += len(text)
                if total_length >= max_length:
                    break
        
        return " ".join(text_parts)
    
    async def fetch_content(self, url: str) -> str:
        """
        Fetch and extract text content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text content
        """
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            return self._extract_text(response.text)
        except Exception as e:
            print(f"[WebSearcher] Fetch error for {url}: {e}")
            return ""
    
    def fetch_content_sync(self, url: str) -> str:
        """Synchronous version of fetch_content."""
        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as client:
                response = client.get(url)
                response.raise_for_status()
                return self._extract_text(response.text)
        except Exception as e:
            print(f"[WebSearcher] Fetch error for {url}: {e}")
            return ""
    
    def research_topic(self, topic: str) -> ResearchData:
        """
        Research a debate topic by searching for multiple perspectives.
        
        Args:
            topic: The debate topic to research
            
        Returns:
            ResearchData with arguments from both sides
        """
        pro_results = self.search_sync(f"{topic} benefits advantages pros arguments", 3)
        con_results = self.search_sync(f"{topic} problems disadvantages cons arguments", 3)
        fact_results = self.search_sync(f"{topic} facts statistics research data", 3)
        
        # Extract key information from snippets
        pro_arguments = [r.snippet for r in pro_results if r.snippet]
        con_arguments = [r.snippet for r in con_results if r.snippet]
        facts = [r.snippet for r in fact_results if r.snippet]
        
        # Collect unique sources
        all_results = pro_results + con_results + fact_results
        sources = list(set(r.url for r in all_results if r.url))
        
        return ResearchData(
            topic=topic,
            pro_arguments=pro_arguments,
            con_arguments=con_arguments,
            facts=facts,
            sources=sources[:10],  # Limit sources
        )
    
    async def research_topic_async(self, topic: str) -> ResearchData:
        """Async version of research_topic."""
        # Run searches in parallel
        pro_task = self.search(f"{topic} benefits advantages pros arguments", 3)
        con_task = self.search(f"{topic} problems disadvantages cons arguments", 3)
        fact_task = self.search(f"{topic} facts statistics research data", 3)
        
        pro_results, con_results, fact_results = await asyncio.gather(
            pro_task, con_task, fact_task
        )
        
        pro_arguments = [r.snippet for r in pro_results if r.snippet]
        con_arguments = [r.snippet for r in con_results if r.snippet]
        facts = [r.snippet for r in fact_results if r.snippet]
        
        all_results = pro_results + con_results + fact_results
        sources = list(set(r.url for r in all_results if r.url))
        
        return ResearchData(
            topic=topic,
            pro_arguments=pro_arguments,
            con_arguments=con_arguments,
            facts=facts,
            sources=sources[:10],
        )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Global instance for reuse
web_searcher = WebSearcher()


def quick_research(topic: str) -> ResearchData:
    """
    Quick synchronous research function for easy use.
    
    Args:
        topic: Debate topic to research
        
    Returns:
        ResearchData with collected information
    """
    return web_searcher.research_topic(topic)
