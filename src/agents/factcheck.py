"""
Fact Check Agent - Verifies claims against retrieved context.
"""

import re
from src.agents.base import Agent, AgentState, DebateContext


class FactCheckAgent(Agent):
    """
    Checks debate arguments against retrieved passages.

    Uses simple heuristics to score claim support:
    - Keyword overlap between claims and sources
    - Source citation presence
    - Consistency checks
    """

    def __init__(self):
        super().__init__("FactCheck")

    def _extract_claims(self, argument: str) -> list[str]:
        """Extract key claims from an argument."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', argument)
        claims = []

        for sent in sentences:
            sent = sent.strip()
            # Filter for substantive claims (longer sentences)
            if len(sent.split()) >= 5:
                claims.append(sent)

        return claims

    def _compute_keyword_overlap(self, text1: str, text2: str) -> float:
        """Compute keyword overlap between two texts."""
        def get_keywords(text):
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            words = text.split()
            # Filter stopwords
            stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be',
                        'been', 'being', 'have', 'has', 'had', 'do', 'does',
                        'did', 'will', 'would', 'could', 'should', 'may',
                        'might', 'must', 'shall', 'can', 'need', 'dare',
                        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with',
                        'at', 'by', 'from', 'as', 'into', 'through', 'during',
                        'before', 'after', 'above', 'below', 'between', 'under',
                        'again', 'further', 'then', 'once', 'here', 'there',
                        'when', 'where', 'why', 'how', 'all', 'each', 'few',
                        'more', 'most', 'other', 'some', 'such', 'no', 'nor',
                        'not', 'only', 'own', 'same', 'so', 'than', 'too',
                        'very', 'just', 'and', 'but', 'if', 'or', 'because',
                        'until', 'while', 'that', 'this', 'these', 'those'}
            return set(w for w in words if len(w) > 3 and w not in stopwords)

        keywords1 = get_keywords(text1)
        keywords2 = get_keywords(text2)

        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        return len(intersection) / len(union) if union else 0.0

    def check_argument(
        self,
        argument: str,
        sources: list[str],
        passages: list[dict],
    ) -> dict:
        """
        Check an argument against source passages.

        Args:
            argument: The debate argument to check
            sources: Source citations in the argument
            passages: Retrieved passages to check against

        Returns:
            Dict with fact check results
        """
        claims = self._extract_claims(argument)
        passage_texts = [p["text"] for p in passages]
        all_passage_text = " ".join(passage_texts)

        # Compute overall support score
        if claims:
            claim_scores = []
            for claim in claims:
                # Check overlap with all passages
                overlap = self._compute_keyword_overlap(claim, all_passage_text)
                claim_scores.append(overlap)

            avg_support = sum(claim_scores) / len(claim_scores)
            max_support = max(claim_scores) if claim_scores else 0
        else:
            avg_support = 0.0
            max_support = 0.0

        # Check source usage
        source_coverage = len(sources) / len(passages) if passages else 0

        # Overall faithfulness score
        faithfulness = (avg_support * 0.6) + (source_coverage * 0.4)

        return {
            "num_claims": len(claims),
            "avg_support_score": avg_support,
            "max_support_score": max_support,
            "source_coverage": source_coverage,
            "faithfulness_score": faithfulness,
            "supported": faithfulness > 0.3,  # Threshold for "supported"
        }

    def process(self, context: DebateContext) -> DebateContext:
        """Fact-check all debate turns."""
        self._log(context, "starting_factcheck", {
            "num_pro_turns": len(context.pro_turns),
            "num_con_turns": len(context.con_turns),
        })

        # Check all pro turns
        for turn in context.pro_turns:
            result = self.check_argument(
                turn.argument,
                turn.sources,
                context.retrieved_passages,
            )
            turn.fact_check_result = result

        # Check all con turns
        for turn in context.con_turns:
            result = self.check_argument(
                turn.argument,
                turn.sources,
                context.retrieved_passages,
            )
            turn.fact_check_result = result

        # Compute aggregate metrics
        all_turns = context.pro_turns + context.con_turns
        if all_turns:
            avg_faithfulness = sum(
                t.fact_check_result["faithfulness_score"] for t in all_turns
            ) / len(all_turns)

            supported_count = sum(
                1 for t in all_turns if t.fact_check_result["supported"]
            )
        else:
            avg_faithfulness = 0
            supported_count = 0

        context.metrics["fact_check"] = {
            "avg_faithfulness": avg_faithfulness,
            "supported_claims_ratio": supported_count / len(all_turns) if all_turns else 0,
            "total_turns_checked": len(all_turns),
        }

        self._log(context, "factcheck_complete", {
            "avg_faithfulness": avg_faithfulness,
        })

        context.current_state = AgentState.JUDGING
        return context
