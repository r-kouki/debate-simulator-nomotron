"""
Research Agent - Retrieves relevant information via web search.

Uses DuckDuckGo for real-time web research on any debate topic.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from src.agents.base import Agent, AgentState, DebateContext
from src.utils.web_search import WebSearcher, ResearchData, quick_research


@dataclass
class Passage:
    """A retrieved passage from research."""
    text: str
    source: str
    score: float
    domain: str
    stance: str = ""  # "pro", "con", or "neutral"


class ResearchAgent(Agent):
    """
    Retrieves relevant information via live web search.

    Searches the internet for topic arguments, facts, and sources.
    """

    def __init__(self, use_web_search: bool = True):
        """
        Initialize research agent.
        
        Args:
            use_web_search: If True, search the web. If False, use cached data only.
        """
        super().__init__("Research")
        self.use_web_search = use_web_search
        self._searcher = WebSearcher(timeout=15.0, max_results=5)
        self._cache: dict[str, ResearchData] = {}

    def _research_to_passages(self, research: ResearchData) -> list[Passage]:
        """Convert ResearchData to list of Passages."""
        passages = []
        
        # Pro arguments
        for i, arg in enumerate(research.pro_arguments):
            passages.append(Passage(
                text=arg,
                source=research.sources[i] if i < len(research.sources) else "web_search",
                score=1.0 - (i * 0.1),
                domain="general",
                stance="pro",
            ))
        
        # Con arguments
        for i, arg in enumerate(research.con_arguments):
            passages.append(Passage(
                text=arg,
                source=research.sources[len(research.pro_arguments) + i] if (len(research.pro_arguments) + i) < len(research.sources) else "web_search",
                score=1.0 - (i * 0.1),
                domain="general",
                stance="con",
            ))
        
        # Facts (neutral)
        for i, fact in enumerate(research.facts):
            passages.append(Passage(
                text=fact,
                source=research.sources[-1] if research.sources else "web_search",
                score=0.9 - (i * 0.1),
                domain="general",
                stance="neutral",
            ))
        
        return passages

    def retrieve(
        self,
        topic: str,
        top_k: int = 10,
    ) -> list[Passage]:
        """
        Retrieve relevant information for a topic via web search.

        Args:
            topic: Search topic
            top_k: Number of passages to retrieve

        Returns:
            List of Passage objects
        """
        # Check cache first
        cache_key = topic.lower().strip()
        if cache_key in self._cache:
            research = self._cache[cache_key]
        elif self.use_web_search:
            # Perform live web search
            print(f"[Research] Searching web for: {topic}")
            try:
                research = quick_research(topic)
                self._cache[cache_key] = research
            except Exception as e:
                print(f"[Research] Web search failed: {e}")
                # Return empty if search fails
                return []
        else:
            return []
        
        passages = self._research_to_passages(research)
        return passages[:top_k]

    def process(self, context: DebateContext) -> DebateContext:
        """Retrieve relevant information for the debate topic."""
        self._log(context, "starting_research", {
            "topic": context.topic,
            "use_web_search": self.use_web_search,
        })

        # Retrieve passages via web search
        passages = self.retrieve(
            topic=context.topic,
            top_k=10,
        )

        context.retrieved_passages = [
            {
                "text": p.text,
                "source": p.source,
                "score": p.score,
                "domain": p.domain,
                "stance": p.stance,
            }
            for p in passages
        ]

        # Separate pro and con passages for the debater
        pro_passages = [p for p in passages if p.stance == "pro"]
        con_passages = [p for p in passages if p.stance == "con"]
        neutral_passages = [p for p in passages if p.stance == "neutral"]

        context.corpus_stats = {
            "num_retrieved": len(passages),
            "num_pro": len(pro_passages),
            "num_con": len(con_passages),
            "num_facts": len(neutral_passages),
            "sources": list(set(p.source for p in passages)),
            "web_search_used": self.use_web_search,
        }

        self._log(context, "research_complete", {
            "num_passages": len(passages),
            "num_sources": len(context.corpus_stats["sources"]),
        })

        context.current_state = AgentState.DEBATING_PRO
        return context

