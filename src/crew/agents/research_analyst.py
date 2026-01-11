"""
Research Analyst Agent - Classifies and structures research data.

Responsibilities:
1. Classify research snippets into PRO/CON/NEUTRAL categories
2. Extract key facts and statistics
3. Structure data for debaters to use effectively
4. Filter out irrelevant or low-quality research
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class ClassifiedResearch:
    """Structured research data for debaters."""
    topic: str
    pro_points: list[str]
    con_points: list[str]
    key_facts: list[str]
    statistics: list[str]
    sources: list[str]
    quality_score: int  # 0-100


@dataclass
class ResearchPoint:
    """A single research point with classification."""
    text: str
    classification: str  # "pro", "con", "neutral", "fact"
    confidence: float  # 0.0-1.0
    has_statistic: bool


def analyze_research(raw_research: str, topic: str) -> ClassifiedResearch:
    """
    Analyze and classify raw research into structured categories.
    
    Args:
        raw_research: Raw research text from search tools
        topic: The debate topic for context
        
    Returns:
        ClassifiedResearch with categorized points
    """
    if not raw_research or len(raw_research) < 50:
        return ClassifiedResearch(
            topic=topic,
            pro_points=[],
            con_points=[],
            key_facts=[],
            statistics=[],
            sources=[],
            quality_score=0,
        )
    
    # Split into individual points/sentences
    points = _extract_points(raw_research)
    
    # Classify each point
    classified = [_classify_point(p, topic) for p in points]
    
    # Separate into categories
    pro_points = []
    con_points = []
    key_facts = []
    statistics = []
    
    for point in classified:
        if point.classification == "pro":
            pro_points.append(point.text)
        elif point.classification == "con":
            con_points.append(point.text)
        elif point.classification == "fact":
            key_facts.append(point.text)
        
        if point.has_statistic:
            statistics.append(point.text)
    
    # Extract sources
    sources = _extract_sources(raw_research)
    
    # Calculate quality score
    quality_score = _calculate_quality_score(pro_points, con_points, key_facts, statistics)
    
    return ClassifiedResearch(
        topic=topic,
        pro_points=pro_points[:5],  # Limit to top 5
        con_points=con_points[:5],
        key_facts=key_facts[:5],
        statistics=statistics[:5],
        sources=sources[:5],
        quality_score=quality_score,
    )


def _extract_points(text: str) -> list[str]:
    """Extract individual points from research text."""
    # Split by common separators
    text = text.replace('\n\n', '\n')
    
    # Split by sentences or bullet points
    points = []
    
    # Handle numbered lists
    numbered = re.split(r'\d+\.\s+', text)
    for item in numbered:
        if len(item.strip()) > 30:
            points.append(item.strip())
    
    # If no numbered items, split by sentences
    if len(points) < 3:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        points = [s.strip() for s in sentences if len(s.strip()) > 30]
    
    # Clean up points
    cleaned = []
    for p in points:
        # Remove markdown formatting
        p = re.sub(r'\*\*([^*]+)\*\*', r'\1', p)
        p = re.sub(r'\*([^*]+)\*', r'\1', p)
        p = re.sub(r'#{1,3}\s*', '', p)
        p = p.strip()
        if len(p) > 30 and p not in cleaned:
            cleaned.append(p)
    
    return cleaned[:15]  # Limit to 15 points


def _classify_point(text: str, topic: str) -> ResearchPoint:
    """Classify a single research point."""
    text_lower = text.lower()
    
    # Pro indicators
    pro_words = [
        "benefit", "advantage", "positive", "improve", "success",
        "help", "support", "growth", "increase", "better",
        "opportunity", "solution", "effective", "efficient",
        "progress", "innovation", "advancement", "gain",
    ]
    
    # Con indicators
    con_words = [
        "problem", "risk", "negative", "concern", "issue",
        "challenge", "threat", "danger", "harm", "cost",
        "failure", "decline", "decrease", "worse", "obstacle",
        "criticism", "controversy", "disadvantage", "drawback",
    ]
    
    # Neutral/fact indicators
    fact_words = [
        "according to", "research shows", "study found",
        "data indicates", "statistics show", "report",
        "survey", "analysis", "evidence", "findings",
    ]
    
    # Check for statistics
    has_stat = bool(re.search(r'\d+[\d,\.]*\s*(%|percent|million|billion)', text_lower))
    
    # Count matches
    pro_score = sum(1 for w in pro_words if w in text_lower)
    con_score = sum(1 for w in con_words if w in text_lower)
    fact_score = sum(1 for w in fact_words if w in text_lower)
    
    # Determine classification
    if fact_score >= 1 and pro_score < 2 and con_score < 2:
        classification = "fact"
        confidence = min(0.9, 0.5 + fact_score * 0.1)
    elif pro_score > con_score + 1:
        classification = "pro"
        confidence = min(0.9, 0.4 + pro_score * 0.1)
    elif con_score > pro_score + 1:
        classification = "con"
        confidence = min(0.9, 0.4 + con_score * 0.1)
    elif has_stat:
        classification = "fact"
        confidence = 0.6
    else:
        classification = "neutral"
        confidence = 0.3
    
    return ResearchPoint(
        text=text,
        classification=classification,
        confidence=confidence,
        has_statistic=has_stat,
    )


def _extract_sources(text: str) -> list[str]:
    """Extract URLs and source references from text."""
    # Find URLs
    urls = re.findall(r'https?://[^\s\)]+', text)
    
    # Find "Source:" references
    sources = re.findall(r'Source:\s*([^\n]+)', text)
    
    # Combine and deduplicate
    all_sources = list(set(urls + sources))
    return [s.strip() for s in all_sources if s.strip()]


def _calculate_quality_score(pro: list, con: list, facts: list, stats: list) -> int:
    """Calculate overall research quality score (0-100)."""
    score = 0
    
    # Points for having pro arguments (max 25)
    score += min(25, len(pro) * 5)
    
    # Points for having con arguments (max 25)
    score += min(25, len(con) * 5)
    
    # Points for facts (max 25)
    score += min(25, len(facts) * 5)
    
    # Points for statistics (max 25)
    score += min(25, len(stats) * 8)
    
    return min(100, score)


def format_for_debater(research: ClassifiedResearch, stance: str) -> str:
    """
    Format research for a specific debater to use.
    
    Args:
        research: Classified research data
        stance: "pro" or "con"
        
    Returns:
        Formatted string optimized for the debater's use
    """
    lines = []
    
    if stance == "pro":
        lines.append("SUPPORTING EVIDENCE FOR YOUR POSITION:")
        for i, point in enumerate(research.pro_points[:3], 1):
            lines.append(f"• {point}")
        
        lines.append("\nOPPONENT'S LIKELY ARGUMENTS (prepare to counter):")
        for i, point in enumerate(research.con_points[:2], 1):
            lines.append(f"• {point}")
    else:
        lines.append("SUPPORTING EVIDENCE FOR YOUR POSITION:")
        for i, point in enumerate(research.con_points[:3], 1):
            lines.append(f"• {point}")
        
        lines.append("\nOPPONENT'S LIKELY ARGUMENTS (prepare to counter):")
        for i, point in enumerate(research.pro_points[:2], 1):
            lines.append(f"• {point}")
    
    if research.statistics:
        lines.append("\nKEY STATISTICS TO CITE:")
        for stat in research.statistics[:2]:
            lines.append(f"• {stat}")
    
    if research.key_facts:
        lines.append("\nNEUTRAL FACTS:")
        for fact in research.key_facts[:2]:
            lines.append(f"• {fact}")
    
    return "\n".join(lines)
