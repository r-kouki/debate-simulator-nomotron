"""
Topic Analyst Agent - Analyzes and prepares debate topics.

Responsibilities:
1. Correct grammar/spelling in the topic
2. Generate optimized research queries
3. Extract key terms for persona search
4. Provide topic context for other agents
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class TopicAnalysis:
    """Result of topic analysis."""
    original_topic: str
    corrected_topic: str
    research_queries: list[str]
    persona_queries: list[str]
    key_terms: list[str]
    domain_hint: str
    is_well_formed: bool


# Common grammar corrections for debate topics
GRAMMAR_CORRECTIONS = {
    "eletric": "electric",
    "vehicals": "vehicles",
    "goverment": "government",
    "enviroment": "environment",
    "enviornment": "environment",
    "benifit": "benefit",
    "benifits": "benefits",
    "recieve": "receive",
    "occured": "occurred",
    "seperate": "separate",
    "untill": "until",
    "thier": "their",
    "accomodate": "accommodate",
    "occurence": "occurrence",
    "definately": "definitely",
    "govermental": "governmental",
    "artifical": "artificial",
    "inteligence": "intelligence",
    "tecnology": "technology",
    "helthcare": "healthcare",
    "educaton": "education",
    "regluation": "regulation",
    "polution": "pollution",
    "pollusion": "pollution",
}


def analyze_topic(topic: str) -> TopicAnalysis:
    """
    Analyze and prepare a debate topic for the pipeline.
    
    Args:
        topic: Raw user-provided topic
        
    Returns:
        TopicAnalysis with corrected topic, research queries, and context
    """
    original = topic.strip()
    
    # Step 1: Correct common grammar/spelling mistakes
    corrected = _correct_grammar(original)
    
    # Step 2: Extract key terms
    key_terms = _extract_key_terms(corrected)
    
    # Step 3: Detect domain
    domain_hint = _detect_domain(corrected, key_terms)
    
    # Step 4: Generate optimized research queries
    research_queries = _generate_research_queries(corrected, key_terms)
    
    # Step 5: Generate persona search queries
    persona_queries = _generate_persona_queries(corrected, key_terms, domain_hint)
    
    # Step 6: Check if topic is well-formed
    is_well_formed = len(key_terms) >= 2 and len(corrected) >= 10
    
    return TopicAnalysis(
        original_topic=original,
        corrected_topic=corrected,
        research_queries=research_queries,
        persona_queries=persona_queries,
        key_terms=key_terms,
        domain_hint=domain_hint,
        is_well_formed=is_well_formed,
    )


def _correct_grammar(topic: str) -> str:
    """Apply common grammar/spelling corrections."""
    corrected = topic.lower()
    
    # Apply known corrections
    for wrong, right in GRAMMAR_CORRECTIONS.items():
        corrected = re.sub(rf'\b{wrong}\b', right, corrected, flags=re.IGNORECASE)
    
    # Capitalize first letter of each major word for display
    words = corrected.split()
    stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    
    capitalized = []
    for i, word in enumerate(words):
        if i == 0 or word not in stop_words:
            capitalized.append(word.capitalize())
        else:
            capitalized.append(word)
    
    return " ".join(capitalized)


def _extract_key_terms(topic: str) -> list[str]:
    """Extract important keywords from the topic."""
    # Remove common stop words
    stop_words = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "better", "best", "more", "most", "other", "such",
        "no", "not", "only", "own", "same", "so", "than", "too", "very",
        "just", "also", "now", "here", "there", "when", "where", "why", "how",
        "all", "each", "every", "both", "few", "more", "most", "some", "any",
    }
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', topic.lower())
    key_terms = [w for w in words if w not in stop_words]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in key_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    
    return unique_terms[:6]  # Limit to 6 key terms


def _detect_domain(topic: str, key_terms: list[str]) -> str:
    """Detect the domain/category of the topic."""
    topic_lower = topic.lower()
    terms_str = " ".join(key_terms)
    
    domain_keywords = {
        "economics": ["economy", "economic", "tax", "taxes", "trade", "market", "gdp", "inflation", "jobs", "employment", "wage", "tariff"],
        "environment": ["climate", "environment", "pollution", "carbon", "emissions", "green", "renewable", "sustainability", "ecology"],
        "technology": ["ai", "artificial", "intelligence", "technology", "tech", "digital", "internet", "software", "automation", "robot"],
        "healthcare": ["health", "healthcare", "medical", "medicine", "hospital", "doctor", "patient", "disease", "vaccine"],
        "education": ["education", "school", "university", "student", "teacher", "learning", "curriculum", "college"],
        "politics": ["government", "political", "policy", "law", "regulation", "democracy", "vote", "election", "congress", "president"],
        "energy": ["energy", "electric", "battery", "solar", "wind", "nuclear", "oil", "gas", "fuel", "power"],
        "social": ["social", "society", "rights", "equality", "justice", "freedom", "immigration", "crime"],
    }
    
    for domain, keywords in domain_keywords.items():
        matches = sum(1 for kw in keywords if kw in topic_lower or kw in terms_str)
        if matches >= 2:
            return domain
    
    return "general"


def _generate_research_queries(topic: str, key_terms: list[str]) -> list[str]:
    """Generate optimized search queries for research."""
    from datetime import datetime
    current_year = datetime.now().year
    
    main_terms = " ".join(key_terms[:3])
    
    queries = [
        # Pro/Con perspectives
        f'"{topic}" arguments for and against {current_year}',
        f'"{topic}" benefits advantages research',
        f'"{topic}" problems criticism concerns',
        
        # Facts and data
        f'{main_terms} statistics data facts {current_year}',
        f'{main_terms} research study findings',
        
        # Expert opinions
        f'{topic} expert analysis opinion',
        f'{main_terms} professor researcher view',
    ]
    
    return queries


def _generate_persona_queries(topic: str, key_terms: list[str], domain: str) -> list[str]:
    """Generate queries for finding debate panelists."""
    main_terms = " ".join(key_terms[:2])
    
    # Domain-specific expert types
    expert_types = {
        "economics": ["economist", "economic professor", "financial analyst"],
        "environment": ["environmental scientist", "climate researcher", "ecologist"],
        "technology": ["technology researcher", "AI expert", "computer scientist"],
        "healthcare": ["medical researcher", "public health expert", "physician"],
        "education": ["education professor", "learning researcher"],
        "politics": ["political scientist", "policy analyst", "political commentator"],
        "energy": ["energy researcher", "renewable energy expert", "engineer"],
        "social": ["sociologist", "social policy expert", "civil rights advocate"],
        "general": ["professor", "researcher", "analyst", "expert"],
    }
    
    expert_roles = expert_types.get(domain, expert_types["general"])
    
    queries = []
    for role in expert_roles[:2]:
        queries.append(f"{main_terms} {role} notable")
        queries.append(f"famous {role} {main_terms}")
    
    # Add general expert queries
    queries.extend([
        f"who is expert on {topic}",
        f"{main_terms} notable scholar academic",
    ])
    
    return queries[:6]


def correct_and_expand_topic(topic: str) -> tuple[str, str]:
    """
    Quick helper to correct topic and get a search-friendly version.
    
    Returns:
        Tuple of (corrected_topic, search_query)
    """
    analysis = analyze_topic(topic)
    search_query = " ".join(analysis.key_terms[:4])
    return (analysis.corrected_topic, search_query)
