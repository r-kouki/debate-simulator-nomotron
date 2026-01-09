"""
Fact Check Agent - Verifies claims against evidence.

Evaluates debate arguments for factual accuracy and
faithfulness to the research context.
"""

from crewai import Agent


def create_factcheck_agent() -> Agent:
    """
    Create the fact-checking agent.
    
    Returns:
        Fact-checker Agent
    """
    return Agent(
        role="Fact Checker",
        goal=(
            "Verify factual claims made in debate arguments. "
            "Assess how well arguments are supported by evidence. "
            "Identify unsupported or misleading claims."
        ),
        backstory=(
            "You are a meticulous fact-checker with experience in journalism and research. "
            "You evaluate claims against available evidence, identify logical fallacies, "
            "and assess the strength of supporting sources. You are objective and thorough, "
            "applying the same scrutiny to both sides of a debate. You provide clear "
            "faithfulness scores based on how well arguments align with cited evidence."
        ),
        verbose=True,
        allow_delegation=False,
    )


def compute_faithfulness_score(
    argument: str,
    research_context: str,
    stopwords: set = None,
) -> dict:
    """
    Compute how well an argument is supported by research.
    
    Uses keyword overlap to estimate faithfulness.
    
    Args:
        argument: The debate argument to check
        research_context: Available research/evidence
        stopwords: Words to exclude from comparison
        
    Returns:
        Dict with faithfulness metrics
    """
    if stopwords is None:
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "to", "of",
            "in", "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once", "and",
            "but", "if", "or", "because", "until", "while", "although",
            "this", "that", "these", "those", "it", "its", "they", "them",
            "their", "we", "our", "you", "your", "i", "my", "me", "he",
            "she", "his", "her", "who", "which", "what", "when", "where",
        }
    
    # Extract claims (sentences with substance)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', argument.strip())
    claims = [s for s in sentences if len(s.split()) >= 5]
    
    if not claims or not research_context:
        return {
            "num_claims": len(claims),
            "avg_support_score": 0.0,
            "faithfulness_score": 0.0,
            "supported_claims": 0,
            "verdict": "insufficient_data",
        }
    
    # Tokenize research context
    research_words = set(
        word.lower() for word in re.findall(r'\b\w+\b', research_context)
        if word.lower() not in stopwords and len(word) > 2
    )
    
    # Score each claim
    claim_scores = []
    for claim in claims:
        claim_words = set(
            word.lower() for word in re.findall(r'\b\w+\b', claim)
            if word.lower() not in stopwords and len(word) > 2
        )
        
        if not claim_words:
            claim_scores.append(0.0)
            continue
        
        # Jaccard-like overlap
        overlap = len(claim_words & research_words)
        score = overlap / len(claim_words)
        claim_scores.append(score)
    
    avg_score = sum(claim_scores) / len(claim_scores) if claim_scores else 0.0
    supported = sum(1 for s in claim_scores if s >= 0.3)
    
    # Determine verdict
    if avg_score >= 0.5:
        verdict = "well_supported"
    elif avg_score >= 0.3:
        verdict = "partially_supported"
    else:
        verdict = "weakly_supported"
    
    return {
        "num_claims": len(claims),
        "avg_support_score": round(avg_score, 3),
        "faithfulness_score": round(avg_score, 3),
        "supported_claims": supported,
        "verdict": verdict,
    }
