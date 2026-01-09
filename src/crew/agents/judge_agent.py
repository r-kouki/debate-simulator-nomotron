"""
Judge Agent - Evaluates debates and declares winners.

Scores arguments based on evidence, reasoning, and civility,
then determines the debate winner.
"""

from dataclasses import dataclass
from crewai import Agent


@dataclass
class JudgeScore:
    """Structured debate scoring result."""
    pro_score: float
    con_score: float
    winner: str  # "pro", "con", or "tie"
    reasoning: str
    criteria: dict


def create_judge_agent() -> Agent:
    """
    Create the judge agent.
    
    Returns:
        Judge Agent
    """
    return Agent(
        role="Debate Judge",
        goal=(
            "Fairly evaluate debate arguments and declare a winner. "
            "Score based on evidence quality, logical reasoning, "
            "response to counter-arguments, and civil discourse."
        ),
        backstory=(
            "You are an impartial debate judge with expertise in argumentation theory. "
            "You evaluate debates using consistent criteria: strength of evidence, "
            "logical coherence, effective rebuttals, and professional tone. "
            "You provide detailed reasoning for your scores and can recognize "
            "when a debate is too close to call (tie). Your judgments are fair, "
            "transparent, and educational."
        ),
        verbose=True,
        allow_delegation=False,
    )


def score_argument(argument: str, research_context: str = "") -> dict:
    """
    Score a single argument using heuristics.
    
    Args:
        argument: The debate argument
        research_context: Available evidence (optional)
        
    Returns:
        Dict with scoring breakdown
    """
    import re
    
    words = argument.split()
    word_count = len(words)
    
    # Length score (normalized)
    length_score = min(word_count / 100, 1.0) * 25
    
    # Logic markers
    logic_markers = [
        "because", "therefore", "thus", "hence", "consequently",
        "as a result", "this means", "it follows", "given that",
        "since", "due to", "leads to", "implies",
    ]
    logic_count = sum(1 for m in logic_markers if m in argument.lower())
    logic_score = min(logic_count * 5, 25)
    
    # Evidence markers
    evidence_markers = [
        "study", "research", "data", "statistics", "percent", "%",
        "according to", "experts", "evidence", "found that",
        "shows that", "demonstrates", "proves", "survey",
    ]
    evidence_count = sum(1 for m in evidence_markers if m in argument.lower())
    evidence_score = min(evidence_count * 5, 25)
    
    # Civility (absence of aggressive language)
    aggressive_markers = [
        "stupid", "idiot", "ridiculous", "absurd", "nonsense",
        "obviously wrong", "completely false", "lying",
    ]
    aggressive_count = sum(1 for m in aggressive_markers if m in argument.lower())
    civility_score = max(25 - aggressive_count * 10, 0)
    
    total = length_score + logic_score + evidence_score + civility_score
    
    return {
        "total": round(total, 1),
        "length": round(length_score, 1),
        "logic": round(logic_score, 1),
        "evidence": round(evidence_score, 1),
        "civility": round(civility_score, 1),
    }


def judge_debate(
    pro_arguments: list[str],
    con_arguments: list[str],
    fact_check_results: dict = None,
) -> JudgeScore:
    """
    Judge a complete debate.
    
    Args:
        pro_arguments: List of pro arguments
        con_arguments: List of con arguments
        fact_check_results: Optional fact-check scores
        
    Returns:
        JudgeScore with winner and reasoning
    """
    # Score all arguments
    pro_scores = [score_argument(arg) for arg in pro_arguments]
    con_scores = [score_argument(arg) for arg in con_arguments]
    
    # Aggregate scores
    pro_total = sum(s["total"] for s in pro_scores) / len(pro_scores) if pro_scores else 0
    con_total = sum(s["total"] for s in con_scores) / len(con_scores) if con_scores else 0
    
    # Factor in fact-check if available
    if fact_check_results:
        pro_faith = fact_check_results.get("pro", {}).get("faithfulness_score", 0.5)
        con_faith = fact_check_results.get("con", {}).get("faithfulness_score", 0.5)
        
        # Faithfulness contributes 30% to final score
        pro_total = pro_total * 0.7 + pro_faith * 30
        con_total = con_total * 0.7 + con_faith * 30
    
    # Determine winner
    margin = abs(pro_total - con_total)
    if margin < 3:
        winner = "tie"
        reasoning = (
            f"This debate is too close to call. "
            f"Pro scored {pro_total:.1f} and Con scored {con_total:.1f}. "
            f"Both sides presented compelling arguments."
        )
    elif pro_total > con_total:
        winner = "pro"
        reasoning = (
            f"Pro wins with a score of {pro_total:.1f} vs {con_total:.1f}. "
            f"The pro side demonstrated stronger evidence and reasoning."
        )
    else:
        winner = "con"
        reasoning = (
            f"Con wins with a score of {con_total:.1f} vs {pro_total:.1f}. "
            f"The con side presented more compelling counter-arguments."
        )
    
    return JudgeScore(
        pro_score=round(pro_total, 1),
        con_score=round(con_total, 1),
        winner=winner,
        reasoning=reasoning,
        criteria={
            "pro_breakdown": pro_scores,
            "con_breakdown": con_scores,
        },
    )
