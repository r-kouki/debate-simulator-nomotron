"""
Research Quality Evaluator - Evaluates and refines search queries.

Scores research output quality and suggests refined queries if needed.
Used to iteratively improve research results up to 5 times.
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class ResearchEvaluation:
    """Result of evaluating research quality."""
    score: int  # 0-100
    is_acceptable: bool  # score >= threshold
    issues: list[str]  # What's wrong
    refined_queries: list[str]  # Better queries to try
    explanation: str


def evaluate_research_quality(
    research_text: str,
    topic: str,
    threshold: int = 60,
) -> ResearchEvaluation:
    """
    Evaluate the quality of research results.
    
    Args:
        research_text: The research content to evaluate
        topic: Original topic being researched
        threshold: Minimum acceptable score (default 60)
        
    Returns:
        ResearchEvaluation with score, issues, and refined queries
    """
    issues = []
    score = 100  # Start perfect, deduct for issues
    
    # Check if research is empty or too short
    if not research_text or len(research_text) < 100:
        return ResearchEvaluation(
            score=0,
            is_acceptable=False,
            issues=["Research is empty or too short"],
            refined_queries=_generate_refined_queries(topic, "empty"),
            explanation="No meaningful research content found"
        )
    
    text_lower = research_text.lower()
    topic_lower = topic.lower()
    topic_words = set(topic_lower.split())
    
    # 1. Check topic relevance (are topic keywords mentioned?)
    topic_mentions = sum(1 for word in topic_words if word in text_lower and len(word) > 3)
    topic_relevance = topic_mentions / max(len(topic_words), 1)
    if topic_relevance < 0.3:
        issues.append("Low topic relevance - research may be off-topic")
        score -= 25
    elif topic_relevance < 0.6:
        issues.append("Moderate topic relevance")
        score -= 10
    
    # 2. Check for specificity (numbers, dates, names)
    has_numbers = bool(re.search(r'\d+[\d,\.]*\s*(%|percent|million|billion|thousand)', text_lower))
    has_years = bool(re.search(r'(19|20)\d{2}', research_text))
    has_quotes = research_text.count('"') >= 2 or research_text.count("'") >= 4
    
    specificity_score = sum([has_numbers, has_years, has_quotes])
    if specificity_score == 0:
        issues.append("No specific data (numbers, dates, or quotes)")
        score -= 20
    elif specificity_score == 1:
        issues.append("Low specificity - needs more concrete data")
        score -= 10
    
    # 3. Check for diversity (both pro and con perspectives)
    pro_indicators = ["benefit", "advantage", "positive", "support", "favor", "help"]
    con_indicators = ["problem", "risk", "negative", "criticism", "concern", "oppose", "downside"]
    
    has_pro = any(ind in text_lower for ind in pro_indicators)
    has_con = any(ind in text_lower for ind in con_indicators)
    
    if not has_pro and not has_con:
        issues.append("Missing both pro and con perspectives")
        score -= 20
    elif not has_pro or not has_con:
        issues.append(f"Missing {'pro' if not has_pro else 'con'} perspective")
        score -= 10
    
    # 4. Check for source quality indicators
    credibility_indicators = [
        "study", "research", "professor", "university", "expert",
        "according to", "report", "analysis", "data shows"
    ]
    has_credibility = sum(1 for ind in credibility_indicators if ind in text_lower)
    if has_credibility == 0:
        issues.append("No credible source indicators")
        score -= 15
    elif has_credibility < 2:
        issues.append("Few credible source references")
        score -= 5
    
    # 5. Check length adequacy
    word_count = len(research_text.split())
    if word_count < 200:
        issues.append("Research too brief")
        score -= 15
    elif word_count < 400:
        issues.append("Research could be more comprehensive")
        score -= 5
    
    # Ensure score stays in bounds
    score = max(0, min(100, score))
    is_acceptable = score >= threshold
    
    # Generate refined queries if not acceptable
    refined_queries = []
    if not is_acceptable:
        primary_issue = "general"
        if "off-topic" in " ".join(issues).lower():
            primary_issue = "relevance"
        elif "specific" in " ".join(issues).lower():
            primary_issue = "specificity"
        elif "pro" in " ".join(issues).lower() or "con" in " ".join(issues).lower():
            primary_issue = "perspective"
        elif "credible" in " ".join(issues).lower():
            primary_issue = "credibility"
        
        refined_queries = _generate_refined_queries(topic, primary_issue)
    
    explanation = f"Score {score}/100. " + (
        "Research quality acceptable." if is_acceptable 
        else f"Issues: {', '.join(issues[:2])}"
    )
    
    return ResearchEvaluation(
        score=score,
        is_acceptable=is_acceptable,
        issues=issues,
        refined_queries=refined_queries,
        explanation=explanation
    )


def _generate_refined_queries(topic: str, issue_type: str) -> list[str]:
    """Generate refined search queries based on the issue type."""
    
    # Get current year for recency
    from datetime import datetime
    current_year = datetime.now().year
    
    base_queries = {
        "empty": [
            f'"{topic}" explanation overview',
            f'what is {topic} guide',
            f'{topic} definition examples',
        ],
        "relevance": [
            f'"{topic}" specifically explained',
            f'"{topic}" detailed analysis',
            f'{topic} main issues debate',
        ],
        "specificity": [
            f'{topic} statistics data {current_year}',
            f'{topic} research study findings',
            f'{topic} numbers facts figures',
            f'{topic} expert analysis report',
        ],
        "perspective": [
            f'{topic} arguments for and against',
            f'{topic} pros cons debate',
            f'{topic} supporters critics views',
            f'why {topic} controversial both sides',
        ],
        "credibility": [
            f'{topic} academic research university',
            f'{topic} expert opinion professor',
            f'{topic} peer reviewed study',
            f'{topic} official report analysis',
        ],
        "general": [
            f'"{topic}" comprehensive analysis {current_year}',
            f'{topic} expert debate arguments evidence',
            f'{topic} research data pros cons',
            f'{topic} detailed explanation impact',
        ],
    }
    
    return base_queries.get(issue_type, base_queries["general"])


def suggest_query_refinement(
    original_query: str,
    research_text: str,
    topic: str,
) -> tuple[bool, list[str]]:
    """
    Quick check if query needs refinement and return suggestions.
    
    Args:
        original_query: The query that produced the research
        research_text: The research results
        topic: The debate topic
        
    Returns:
        Tuple of (needs_refinement, refined_queries)
    """
    evaluation = evaluate_research_quality(research_text, topic)
    return (not evaluation.is_acceptable, evaluation.refined_queries)
