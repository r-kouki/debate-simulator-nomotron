"""
Logger Agent - Logs metrics and artifacts for evaluation.
"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from src.agents.base import Agent, AgentState, DebateContext


class LoggerAgent(Agent):
    """
    Logs all debate metrics and artifacts to disk.

    Produces:
    - Structured JSON metrics
    - Human-readable debate transcript
    - Agent execution logs
    """

    def __init__(self, output_dir: Path | None = None):
        super().__init__("Logger")
        self.output_dir = output_dir or Path("runs/debates")

    def _serialize_context(self, context: DebateContext) -> dict:
        """Serialize debate context to JSON-compatible dict."""
        return {
            "topic": context.topic,
            "domain": context.domain,
            "num_rounds": context.num_rounds,
            "started_at": context.started_at,
            "completed_at": context.completed_at,
            "pro_turns": [
                {
                    "stance": t.stance,
                    "argument": t.argument,
                    "sources": t.sources,
                    "fact_check": t.fact_check_result,
                    "timestamp": t.timestamp,
                }
                for t in context.pro_turns
            ],
            "con_turns": [
                {
                    "stance": t.stance,
                    "argument": t.argument,
                    "sources": t.sources,
                    "fact_check": t.fact_check_result,
                    "timestamp": t.timestamp,
                }
                for t in context.con_turns
            ],
            "retrieved_passages": context.retrieved_passages,
            "corpus_stats": context.corpus_stats,
            "judge_score": {
                "pro_score": context.judge_score.pro_score,
                "con_score": context.judge_score.con_score,
                "winner": context.judge_score.winner,
                "reasoning": context.judge_score.reasoning,
                "criteria_scores": context.judge_score.criteria_scores,
            } if context.judge_score else None,
            "metrics": context.metrics,
            "agent_logs": context.agent_logs,
        }

    def _generate_transcript(self, context: DebateContext) -> str:
        """Generate human-readable debate transcript."""
        lines = []
        lines.append("=" * 60)
        lines.append("DEBATE TRANSCRIPT")
        lines.append("=" * 60)
        lines.append(f"\nTopic: {context.topic}")
        lines.append(f"Domain: {context.domain}")
        lines.append(f"Date: {context.started_at}")
        lines.append("")

        # Interleave pro and con turns
        max_turns = max(len(context.pro_turns), len(context.con_turns))

        for i in range(max_turns):
            if i < len(context.pro_turns):
                turn = context.pro_turns[i]
                lines.append(f"\n--- Round {i+1}: PRO ---")
                lines.append(turn.argument)
                if turn.fact_check_result:
                    fc = turn.fact_check_result
                    lines.append(f"[Faithfulness: {fc['faithfulness_score']:.2f}]")

            if i < len(context.con_turns):
                turn = context.con_turns[i]
                lines.append(f"\n--- Round {i+1}: CON ---")
                lines.append(turn.argument)
                if turn.fact_check_result:
                    fc = turn.fact_check_result
                    lines.append(f"[Faithfulness: {fc['faithfulness_score']:.2f}]")

        # Add judgment
        if context.judge_score:
            lines.append("\n" + "=" * 60)
            lines.append("JUDGMENT")
            lines.append("=" * 60)
            lines.append(f"\nPro Score: {context.judge_score.pro_score:.2f}/10")
            lines.append(f"Con Score: {context.judge_score.con_score:.2f}/10")
            lines.append(f"Winner: {context.judge_score.winner.upper()}")
            lines.append(f"\nReasoning: {context.judge_score.reasoning}")

        return "\n".join(lines)

    def save_artifacts(self, context: DebateContext) -> dict[str, Path]:
        """
        Save all debate artifacts to disk.

        Returns:
            Dict mapping artifact names to file paths
        """
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debate_dir = self.output_dir / timestamp
        debate_dir.mkdir(parents=True, exist_ok=True)

        artifacts = {}

        # Save JSON data
        json_path = debate_dir / "debate_data.json"
        with open(json_path, 'w') as f:
            json.dump(self._serialize_context(context), f, indent=2)
        artifacts["json_data"] = json_path

        # Save transcript
        transcript_path = debate_dir / "transcript.txt"
        with open(transcript_path, 'w') as f:
            f.write(self._generate_transcript(context))
        artifacts["transcript"] = transcript_path

        # Save metrics summary
        metrics_path = debate_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(context.metrics, f, indent=2)
        artifacts["metrics"] = metrics_path

        # Save agent logs
        logs_path = debate_dir / "agent_logs.json"
        with open(logs_path, 'w') as f:
            json.dump(context.agent_logs, f, indent=2)
        artifacts["agent_logs"] = logs_path

        return artifacts

    def process(self, context: DebateContext) -> DebateContext:
        """Log all debate artifacts."""
        self._log(context, "starting_logging", {})

        # Mark completion time
        context.completed_at = datetime.now().isoformat()

        # Save artifacts
        artifacts = self.save_artifacts(context)

        # Record artifact paths in metrics
        context.metrics["artifacts"] = {
            name: str(path) for name, path in artifacts.items()
        }

        self._log(context, "logging_complete", {
            "num_artifacts": len(artifacts),
            "output_dir": str(self.output_dir),
        })

        context.current_state = AgentState.COMPLETE
        return context
