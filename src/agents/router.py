"""
Domain Router Agent - Routes topics to appropriate domain adapters.
"""

import re
from src.agents.base import Agent, AgentState, DebateContext


# Domain keywords for classification
DOMAIN_KEYWORDS = {
    "education": [
        "school", "student", "teacher", "university", "college", "curriculum",
        "learning", "education", "academic", "classroom", "homework", "exam",
        "degree", "tuition", "professor", "lecture", "study", "grade",
        "standardized test", "online learning", "coding", "STEM"
    ],
    "technology": [
        "AI", "artificial intelligence", "technology", "software", "computer",
        "internet", "digital", "algorithm", "data", "privacy", "automation",
        "robot", "machine learning", "social media", "smartphone", "crypto",
        "blockchain", "cybersecurity", "programming"
    ],
    "ecology": [
        "environment", "climate", "carbon", "renewable", "pollution",
        "conservation", "wildlife", "ecosystem", "sustainable", "green",
        "recycling", "deforestation", "biodiversity", "ocean", "plastic",
        "emissions", "energy", "solar", "wind power"
    ],
    "medicine": [
        "health", "medical", "doctor", "hospital", "disease", "vaccine",
        "pharmaceutical", "treatment", "patient", "surgery", "diagnosis",
        "mental health", "healthcare", "drug", "therapy", "clinical",
        "epidemic", "wellness", "nutrition"
    ],
}


class DomainRouterAgent(Agent):
    """
    Routes debate topics to the appropriate domain adapter.

    Uses keyword matching to classify topics. Falls back to
    'education' if no clear domain is detected.
    """

    def __init__(self):
        super().__init__("DomainRouter")
        self.domain_keywords = DOMAIN_KEYWORDS
        self.available_domains = list(DOMAIN_KEYWORDS.keys())

    def _classify_topic(self, topic: str) -> tuple[str, float]:
        """
        Classify a topic into a domain.

        Args:
            topic: The debate topic

        Returns:
            Tuple of (domain, confidence_score)
        """
        topic_lower = topic.lower()
        scores = {}

        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in topic_lower:
                    # Longer keywords get higher weight
                    score += len(keyword.split())
            scores[domain] = score

        # Find best match
        best_domain = max(scores, key=scores.get)
        total_score = sum(scores.values())

        if total_score > 0:
            confidence = scores[best_domain] / total_score
        else:
            confidence = 0.0

        return best_domain, confidence

    def process(self, context: DebateContext) -> DebateContext:
        """Route the topic to appropriate domain."""
        self._log(context, "starting_routing", {"topic": context.topic})

        # Classify the topic
        domain, confidence = self._classify_topic(context.topic)

        # If confidence is too low, default to education
        if confidence < 0.2:
            domain = "education"
            confidence = 0.5  # Default confidence

        context.domain = domain
        context.metrics["routing"] = {
            "selected_domain": domain,
            "confidence": confidence,
            "available_domains": self.available_domains,
        }

        self._log(context, "routing_complete", {
            "domain": domain,
            "confidence": confidence,
        })

        context.current_state = AgentState.RESEARCHING
        return context
