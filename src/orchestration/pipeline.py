"""
Debate Pipeline - State machine orchestration for multi-agent debate.

Implements a graph-based orchestration where each agent transitions
the debate context to the next appropriate state.
"""

from pathlib import Path
from datetime import datetime
from typing import Callable

from src.agents.base import Agent, AgentState, DebateContext
from src.agents.router import DomainRouterAgent
from src.agents.research import ResearchAgent
from src.agents.debater import DebaterAgent
from src.agents.factcheck import FactCheckAgent
from src.agents.judge import JudgeAgent
from src.agents.logger import LoggerAgent


class DebatePipeline:
    """
    Orchestrates the multi-agent debate system.

    Uses a state machine pattern where:
    1. Each state maps to an agent
    2. Agents process the context and set the next state
    3. Pipeline runs until COMPLETE or ERROR state

    State flow:
        INIT → ROUTING → RESEARCHING → DEBATING_PRO → DEBATING_CON
        → (repeat for num_rounds) → FACT_CHECKING → JUDGING → LOGGING → COMPLETE
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        model=None,
        tokenizer=None,
        use_adapter: bool = True,
    ):
        """
        Initialize the debate pipeline.

        Args:
            output_dir: Directory for saving debate artifacts
            model: Pre-loaded model (optional)
            tokenizer: Pre-loaded tokenizer (optional)
            use_adapter: Whether to use domain adapters
        """
        self.output_dir = output_dir or Path("runs/debates")

        # Initialize agents
        self.router = DomainRouterAgent()
        self.research = ResearchAgent()
        self.debater_pro = DebaterAgent(
            stance="pro",
            model=model,
            tokenizer=tokenizer,
            use_adapter=use_adapter,
        )
        self.debater_con = DebaterAgent(
            stance="con",
            model=model,
            tokenizer=tokenizer,
            use_adapter=use_adapter,
        )
        self.factcheck = FactCheckAgent()
        self.judge = JudgeAgent()
        self.logger = LoggerAgent(output_dir=self.output_dir)

        # State → Agent mapping
        self.state_handlers: dict[AgentState, Agent] = {
            AgentState.ROUTING: self.router,
            AgentState.RESEARCHING: self.research,
            AgentState.DEBATING_PRO: self.debater_pro,
            AgentState.DEBATING_CON: self.debater_con,
            AgentState.FACT_CHECKING: self.factcheck,
            AgentState.JUDGING: self.judge,
            AgentState.LOGGING: self.logger,
        }

        # Hooks for monitoring
        self.on_state_change: Callable[[DebateContext], None] | None = None

    def _process_state(self, context: DebateContext) -> DebateContext:
        """Process the current state and transition to next."""
        current_state = context.current_state

        if current_state in (AgentState.COMPLETE, AgentState.ERROR):
            return context

        handler = self.state_handlers.get(current_state)
        if handler is None:
            context.error_message = f"No handler for state: {current_state}"
            context.current_state = AgentState.ERROR
            return context

        try:
            context = handler.process(context)

            if self.on_state_change:
                self.on_state_change(context)

        except Exception as e:
            context.error_message = f"Error in {handler.name}: {str(e)}"
            context.current_state = AgentState.ERROR
            import traceback
            context.log_agent_action(
                handler.name,
                "error",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

        return context

    def run(
        self,
        topic: str,
        num_rounds: int = 2,
        verbose: bool = True,
    ) -> DebateContext:
        """
        Run a complete debate on the given topic.

        Args:
            topic: The debate topic
            num_rounds: Number of pro/con exchange rounds
            verbose: Print progress to stdout

        Returns:
            Completed DebateContext with all results
        """
        # Initialize context
        context = DebateContext(
            topic=topic,
            num_rounds=num_rounds,
            current_state=AgentState.ROUTING,
        )

        if verbose:
            print("=" * 60)
            print("MULTI-AGENT DEBATE SIMULATOR")
            print("=" * 60)
            print(f"Topic: {topic}")
            print(f"Rounds: {num_rounds}")
            print()

        # Run state machine
        max_iterations = 100  # Safety limit
        iteration = 0

        while context.current_state not in (AgentState.COMPLETE, AgentState.ERROR):
            if iteration >= max_iterations:
                context.error_message = "Max iterations exceeded"
                context.current_state = AgentState.ERROR
                break

            if verbose:
                print(f"State: {context.current_state.value}")

            context = self._process_state(context)
            iteration += 1

        # Final status
        if verbose:
            print()
            if context.current_state == AgentState.COMPLETE:
                print("✓ Debate completed successfully!")
                if context.judge_score:
                    print(f"\nResult: {context.judge_score.winner.upper()}")
                    print(f"Pro: {context.judge_score.pro_score:.2f} | Con: {context.judge_score.con_score:.2f}")
            else:
                print(f"✗ Debate failed: {context.error_message}")

        return context

    def run_batch(
        self,
        topics: list[str],
        num_rounds: int = 2,
        verbose: bool = False,
    ) -> list[DebateContext]:
        """
        Run debates on multiple topics.

        Args:
            topics: List of debate topics
            num_rounds: Rounds per debate
            verbose: Print progress

        Returns:
            List of completed DebateContext objects
        """
        results = []

        for i, topic in enumerate(topics, 1):
            if verbose:
                print(f"\n[Debate {i}/{len(topics)}]")

            context = self.run(topic, num_rounds=num_rounds, verbose=verbose)
            results.append(context)

        return results

    def get_aggregate_metrics(self, contexts: list[DebateContext]) -> dict:
        """
        Compute aggregate metrics across multiple debates.

        Args:
            contexts: List of completed debate contexts

        Returns:
            Dict with aggregate statistics
        """
        completed = [c for c in contexts if c.current_state == AgentState.COMPLETE]

        if not completed:
            return {"error": "No completed debates"}

        # Win rates
        pro_wins = sum(1 for c in completed if c.judge_score and c.judge_score.winner == "pro")
        con_wins = sum(1 for c in completed if c.judge_score and c.judge_score.winner == "con")
        ties = sum(1 for c in completed if c.judge_score and c.judge_score.winner == "tie")

        # Average scores
        pro_scores = [c.judge_score.pro_score for c in completed if c.judge_score]
        con_scores = [c.judge_score.con_score for c in completed if c.judge_score]

        # Faithfulness metrics
        faithfulness_scores = []
        for c in completed:
            if "fact_check" in c.metrics:
                faithfulness_scores.append(c.metrics["fact_check"]["avg_faithfulness"])

        return {
            "total_debates": len(contexts),
            "completed_debates": len(completed),
            "failed_debates": len(contexts) - len(completed),
            "win_rates": {
                "pro": pro_wins / len(completed) if completed else 0,
                "con": con_wins / len(completed) if completed else 0,
                "tie": ties / len(completed) if completed else 0,
            },
            "average_scores": {
                "pro": sum(pro_scores) / len(pro_scores) if pro_scores else 0,
                "con": sum(con_scores) / len(con_scores) if con_scores else 0,
            },
            "avg_faithfulness": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0,
        }
