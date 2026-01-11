"""
Wikipedia Search Tool - Search Wikipedia for topics and experts.

Provides structured access to Wikipedia for:
- Topic summaries and educational content
- Notable people/experts on specific subjects
- Reliable source information for debates
"""

import hashlib
from typing import Optional
from dataclasses import dataclass, field
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False


class WikipediaSearchInput(BaseModel):
    """Input schema for Wikipedia search."""
    query: str = Field(..., description="The search query")
    search_type: str = Field(
        default="summary",
        description="Type of search: 'summary' (topic overview), 'experts' (notable people), or 'full' (detailed article)"
    )
    sentences: int = Field(
        default=5,
        description="Number of sentences for summary (1-10)"
    )


@dataclass
class Person:
    """Represents a notable person found on Wikipedia."""
    name: str
    bio: str
    url: str
    categories: list = field(default_factory=list)


@dataclass
class WikiCache:
    """Per-session cache for Wikipedia results."""
    results: dict = field(default_factory=dict)
    
    def get_key(self, query: str, search_type: str) -> str:
        """Generate cache key."""
        content = f"{query.lower().strip()}:{search_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, search_type: str) -> Optional[dict]:
        """Get cached results."""
        key = self.get_key(query, search_type)
        return self.results.get(key)
    
    def set(self, query: str, search_type: str, data: dict):
        """Cache results."""
        key = self.get_key(query, search_type)
        self.results[key] = data
    
    def clear(self):
        """Clear cache."""
        self.results.clear()


class WikipediaSearchTool(BaseTool):
    """
    CrewAI tool for Wikipedia searches.
    
    Features:
    - Topic summaries for educational content
    - Expert/notable person discovery
    - Session-based caching
    - Disambiguation handling
    """
    
    name: str = "Wikipedia Search"
    description: str = (
        "Search Wikipedia for topic summaries, notable people/experts, "
        "or detailed article content. Returns reliable, sourced information."
    )
    args_schema: type[BaseModel] = WikipediaSearchInput
    
    # Instance attributes
    language: str = "en"
    _cache: WikiCache = None
    
    def __init__(self, language: str = "en", **kwargs):
        """
        Initialize Wikipedia tool.
        
        Args:
            language: Wikipedia language code (default: 'en')
        """
        super().__init__(**kwargs)
        self.language = language
        self._cache = WikiCache()
        
        if WIKIPEDIA_AVAILABLE:
            wikipedia.set_lang(language)
    
    def _run(self, query: str, search_type: str = "summary", sentences: int = 5) -> str:
        """
        Execute Wikipedia search.
        
        Args:
            query: Search query
            search_type: 'summary', 'experts', or 'full'
            sentences: Number of sentences for summary
            
        Returns:
            Formatted string with Wikipedia results
        """
        if not WIKIPEDIA_AVAILABLE:
            return "Wikipedia package not installed. Run: pip install wikipedia"
        
        # Clamp sentences to valid range
        sentences = max(1, min(10, sentences))
        
        # Check cache
        cached = self._cache.get(query, search_type)
        if cached:
            return self._format_results(cached, from_cache=True)
        
        try:
            if search_type == "experts":
                results = self._search_experts(query)
            elif search_type == "full":
                results = self._search_full(query)
            else:
                results = self._search_summary(query, sentences)
            
            self._cache.set(query, search_type, results)
            return self._format_results(results, from_cache=False)
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation pages
            return self._handle_disambiguation(query, e.options[:5])
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{query}'."
        except Exception as e:
            return f"Wikipedia search failed: {str(e)}"
    
    def _search_summary(self, query: str, sentences: int) -> dict:
        """Get a topic summary."""
        summary = wikipedia.summary(query, sentences=sentences)
        page = wikipedia.page(query, auto_suggest=True)
        
        return {
            "type": "summary",
            "title": page.title,
            "summary": summary,
            "url": page.url,
            "categories": page.categories[:5],
        }
    
    def _search_full(self, query: str) -> dict:
        """Get full article content."""
        page = wikipedia.page(query, auto_suggest=True)
        
        return {
            "type": "full",
            "title": page.title,
            "content": page.content[:3000],  # Limit content length
            "url": page.url,
            "categories": page.categories[:10],
            "links": page.links[:20],
        }
    
    def _search_experts(self, query: str) -> dict:
        """Search for experts/notable people on a topic."""
        # Search for people related to the topic
        search_queries = [
            f"{query} expert",
            f"{query} scientist",
            f"{query} researcher",
            f"{query} scholar",
            f"{query} advocate",
        ]
        
        people = []
        seen_names = set()
        
        for sq in search_queries:
            try:
                results = wikipedia.search(sq, results=3)
                for result in results:
                    if result in seen_names:
                        continue
                    
                    try:
                        page = wikipedia.page(result, auto_suggest=False)
                        # Check if it's likely a person (heuristic)
                        if self._is_likely_person(page):
                            people.append({
                                "name": page.title,
                                "bio": wikipedia.summary(result, sentences=2),
                                "url": page.url,
                                "categories": [c for c in page.categories[:5] if "born" not in c.lower()],
                            })
                            seen_names.add(result)
                    except:
                        continue
                    
                    if len(people) >= 5:
                        break
            except:
                continue
            
            if len(people) >= 5:
                break
        
        return {
            "type": "experts",
            "topic": query,
            "people": people,
        }
    
    def _is_likely_person(self, page) -> bool:
        """
        Check if a Wikipedia page is likely about a person.
        
        Uses strict criteria:
        - Must have "Living people" category OR birth year in categories
        - Must have occupation-related content
        - Must NOT be an event, policy, organization, or concept
        """
        categories_text = " ".join(page.categories).lower()
        content_start = page.content[:800].lower()
        
        # STRONG person indicators (need at least one)
        strong_person_indicators = [
            "living people" in categories_text,
            "births" in categories_text,  # "1950 births", "1980 births", etc.
            "deaths" in categories_text,
            "alumni" in categories_text,
        ]
        
        # If no strong indicator, this is likely not a person
        if not any(strong_person_indicators):
            return False
        
        # Occupation indicators in content (should have at least one)
        occupation_indicators = [
            "is a ", "is an ", "was a ", "was an ",
            "born", "economist", "professor", "scientist",
            "researcher", "journalist", "author", "politician",
            "activist", "director", "analyst", "expert",
        ]
        has_occupation = any(ind in content_start for ind in occupation_indicators)
        
        # DISQUALIFYING patterns - these indicate it's NOT a person
        disqualifying_patterns = [
            "presidency of", "administration of", "government of",
            "is a term", "is a concept", "refers to",
            "was an event", "is a policy", "is a company",
            "is an organization", "is a political party",
            "is a movement", "was a war", "is a treaty",
        ]
        
        for pattern in disqualifying_patterns:
            if pattern in content_start:
                return False
        
        return has_occupation
    
    def _handle_disambiguation(self, query: str, options: list) -> str:
        """Handle disambiguation pages."""
        lines = [
            f"'{query}' is ambiguous. Did you mean one of these?\n",
        ]
        for i, option in enumerate(options, 1):
            lines.append(f"{i}. {option}")
        
        lines.append("\nTry searching with a more specific term.")
        return "\n".join(lines)
    
    def _format_results(self, results: dict, from_cache: bool) -> str:
        """Format results as readable string."""
        cache_note = " (cached)" if from_cache else ""
        lines = []
        
        if results["type"] == "summary":
            lines.append(f"## Wikipedia{cache_note}: {results['title']}\n")
            lines.append(results["summary"])
            lines.append(f"\n**Source**: {results['url']}")
            if results.get("categories"):
                lines.append(f"\n**Categories**: {', '.join(results['categories'][:3])}")
        
        elif results["type"] == "full":
            lines.append(f"## Wikipedia Article{cache_note}: {results['title']}\n")
            lines.append(results["content"])
            lines.append(f"\n**Source**: {results['url']}")
        
        elif results["type"] == "experts":
            lines.append(f"## Experts on {results['topic']}{cache_note}\n")
            
            if not results["people"]:
                lines.append("No notable experts found on Wikipedia.")
            else:
                for i, person in enumerate(results["people"], 1):
                    lines.append(f"### {i}. {person['name']}")
                    lines.append(f"{person['bio']}")
                    lines.append(f"**Wikipedia**: {person['url']}\n")
        
        return "\n".join(lines)
    
    def search_experts_for_debate(self, topic: str) -> list[Person]:
        """
        Search for debate panel recommendations.
        
        Args:
            topic: Debate topic
            
        Returns:
            List of Person objects suitable for debate panel
        """
        results = self._search_experts(topic)
        
        people = []
        for p in results.get("people", []):
            people.append(Person(
                name=p["name"],
                bio=p["bio"],
                url=p["url"],
                categories=p.get("categories", []),
            ))
        
        return people
    
    def clear_cache(self):
        """Clear the session cache."""
        self._cache.clear()
