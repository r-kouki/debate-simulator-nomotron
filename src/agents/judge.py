"""
Judge Agent - Evaluates debate and outputs structured scores.
"""

import re
from src.agents.base import Agent, AgentState, DebateContext, JudgeScore


class JudgeAgent(Agent):
    """
    Judges the debate and produces structured scoring.

    Evaluates based on:
    - Argument strength (logic, evidence)
    - Rebuttal effectiveness
    - Source usage
    - Fact-check results
    """

    def __init__(self):
        super().__init__("Judge")

    def _score_argument_quality(self, argument: str) -> dict:
        """Score the quality of a single argument."""
        # Length-based proxy for thoroughness
        word_count = len(argument.split())
        length_score = min(word_count / 100, 1.0) * 10

        # Check for logical connectors
        logical_markers = [
            'because', 'therefore', 'thus', 'hence', 'consequently',
            'furthermore', 'moreover', 'however', 'nevertheless',
            'first', 'second', 'finally', 'in conclusion'
        ]
        logic_count = sum(1 for m in logical_markers if m in argument.lower())
        logic_score = min(logic_count / 3, 1.0) * 10

        # Check for evidence indicators
        evidence_markers = [
            'study', 'research', 'data', 'statistics', 'survey',
            'according to', 'evidence', 'shows', 'demonstrates',
            'percent', '%', 'report', 'analysis'
        ]
        evidence_count = sum(1 for m in evidence_markers if m in argument.lower())
        evidence_score = min(evidence_count / 2, 1.0) * 10

        return {
            "length_score": length_score,
            "logic_score": logic_score,
            "evidence_score": evidence_score,
            "overall": (length_score + logic_score + evidence_score) / 3,
        }

    def _evaluate_side(self, turns: list, fact_check_weight: float = 0.3) -> dict:
        """Evaluate all turns for one side of the debate."""
        if not turns:
            return {"total_score": 0, "breakdown": {}}

        scores = []
        for turn in turns:
            arg_quality = self._score_argument_quality(turn.argument)

            # Incorporate fact-check if available
            if turn.fact_check_result:
                faithfulness = turn.fact_check_result["faithfulness_score"] * 10
            else:
                faithfulness = 5  # Neutral if not checked

            # Combined score
            combined = (
                arg_quality["overall"] * (1 - fact_check_weight) +
                faithfulness * fact_check_weight
            )
            scores.append({
                "argument_quality": arg_quality,
                "faithfulness": faithfulness,
                "combined": combined,
            })

        avg_score = sum(s["combined"] for s in scores) / len(scores)

        return {
            "total_score": avg_score,
            "num_arguments": len(turns),
            "per_turn_scores": scores,
        }

    def judge_debate(self, context: DebateContext) -> JudgeScore:
        """
        Judge the debate and determine a winner.

        Args:
            context: Complete debate context

        Returns:
            JudgeScore with structured evaluation
        """
        pro_eval = self._evaluate_side(context.pro_turns)
        con_eval = self._evaluate_side(context.con_turns)

        pro_score = pro_eval["total_score"]
        con_score = con_eval["total_score"]

        # Determine winner
        margin = abs(pro_score - con_score)
        if margin < 0.5:
            winner = "tie"
        elif pro_score > con_score:
            winner = "pro"
        else:
            winner = "con"

        # Build reasoning
        reasoning_parts = []
        if winner == "tie":
            reasoning_parts.append("The debate was closely contested with both sides presenting comparable arguments.")
        else:
            winner_name = "Pro" if winner == "pro" else "Con"
            reasoning_parts.append(f"The {winner_name} side presented stronger arguments.")

        if pro_eval.get("per_turn_scores"):
            pro_avg_quality = sum(
                s["argument_quality"]["overall"] for s in pro_eval["per_turn_scores"]
            ) / len(pro_eval["per_turn_scores"])
            reasoning_parts.append(f"Pro average argument quality: {pro_avg_quality:.1f}/10.")

        if con_eval.get("per_turn_scores"):
            con_avg_quality = sum(
                s["argument_quality"]["overall"] for s in con_eval["per_turn_scores"]
            ) / len(con_eval["per_turn_scores"])
            reasoning_parts.append(f"Con average argument quality: {con_avg_quality:.1f}/10.")

        return JudgeScore(
            pro_score=pro_score,
            con_score=con_score,
            winner=winner,
            reasoning=" ".join(reasoning_parts),
            criteria_scores={
                "pro": {
                    "total": pro_score,
                    "breakdown": pro_eval,
                },
                "con": {
                    "total": con_score,
                    "breakdown": con_eval,
                },
            }
        )

    def process(self, context: DebateContext) -> DebateContext:
        """Judge the debate and update context."""
        self._log(context, "starting_judgment", {
            "num_pro_turns": len(context.pro_turns),
            "num_con_turns": len(context.con_turns),
        })

        # Judge the debate
        score = self.judge_debate(context)
        context.judge_score = score

        # Add to metrics
        context.metrics["judgment"] = {
            "pro_score": score.pro_score,
            "con_score": score.con_score,
            "winner": score.winner,
            "margin": abs(score.pro_score - score.con_score),
        }

        self._log(context, "judgment_complete", {
            "winner": score.winner,
            "pro_score": score.pro_score,
            "con_score": score.con_score,
        })

        context.current_state = AgentState.LOGGING
        return context
