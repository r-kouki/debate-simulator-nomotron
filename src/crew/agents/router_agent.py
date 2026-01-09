"""
Domain Router Agent - Routes topics to appropriate domain adapters.

Classifies debate topics into domains (education, medicine, ecology, etc.)
to enable domain-specific adapter loading.
"""

from crewai import Agent


DOMAIN_KEYWORDS = {
    "education": [
        "school", "university", "student", "teacher", "learning", "curriculum",
        "education", "academic", "classroom", "degree", "college", "tuition",
        "homework", "exam", "grading", "literacy", "pedagogy", "scholarship",
    ],
    "medicine": [
        "health", "medical", "doctor", "hospital", "treatment", "disease",
        "patient", "drug", "pharmaceutical", "vaccine", "surgery", "diagnosis",
        "clinical", "therapy", "mental health", "healthcare", "nursing",
    ],
    "ecology": [
        "environment", "climate", "pollution", "ecosystem", "biodiversity",
        "conservation", "sustainability", "carbon", "renewable", "wildlife",
        "deforestation", "ocean", "species", "green", "emission", "nature",
    ],
    "technology": [
        "ai", "artificial intelligence", "robot", "software", "computer",
        "digital", "internet", "cyber", "automation", "algorithm", "data",
        "privacy", "social media", "tech", "innovation", "machine learning",
    ],
}


def classify_domain(topic: str) -> tuple[str, float]:
    """
    Classify a topic into a domain.
    
    Args:
        topic: The debate topic
        
    Returns:
        Tuple of (domain, confidence)
    """
    topic_lower = topic.lower()
    scores = {}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in topic_lower)
        scores[domain] = matches / len(keywords)
    
    best_domain = max(scores, key=scores.get)
    confidence = scores[best_domain]
    
    # Default to "debate" (general) if confidence too low
    if confidence < 0.05:
        return "debate", 0.0
    
    return best_domain, confidence


def create_router_agent() -> Agent:
    """
    Create the domain router agent.
    
    This agent identifies the domain category for debate topics
    to enable appropriate adapter selection.
    """
    return Agent(
        role="Domain Router",
        goal=(
            "Accurately identify the domain category for debate topics "
            "to enable domain-specific expertise and knowledge."
        ),
        backstory=(
            "You are an expert at categorizing topics across multiple domains. "
            "Your classifications help ensure debates leverage specialized knowledge "
            "in education, medicine, ecology, technology, or general debate domains. "
            "You analyze topic keywords and context to make precise categorizations."
        ),
        verbose=True,
        allow_delegation=False,
    )
