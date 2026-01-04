#!/usr/bin/env python3
"""
Phase 5: Run Multi-Agent Debate

Executes the full multi-agent debate pipeline on a given topic.

Run from project root:
    python scripts/run_debate.py "Should standardized testing be abolished?"
    python scripts/run_debate.py --topic "AI in education" --rounds 3
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.model_loader import load_base_model
from src.orchestration.pipeline import DebatePipeline


def main():
    parser = argparse.ArgumentParser(description="Run a multi-agent debate")
    parser.add_argument(
        "topic",
        nargs="?",
        default="Should coding be mandatory in K-12 education?",
        help="The debate topic"
    )
    parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=2,
        help="Number of debate rounds (default: 2)"
    )
    parser.add_argument(
        "--no-adapter",
        action="store_true",
        help="Don't use domain-specific adapters"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=PROJECT_ROOT / "runs" / "debates",
        help="Output directory for artifacts"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("PHASE 5: Multi-Agent Debate System")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Topic: {args.topic}")
    print(f"Rounds: {args.rounds}")
    print(f"Use adapter: {not args.no_adapter}")
    print()

    # Load model once (shared across agents)
    print("--- Loading Model ---")
    model, tokenizer = load_base_model()
    print("Model loaded successfully")
    print()

    # Create pipeline
    pipeline = DebatePipeline(
        output_dir=args.output_dir,
        model=model,
        tokenizer=tokenizer,
        use_adapter=not args.no_adapter,
    )

    # Run debate
    print("--- Starting Debate ---")
    context = pipeline.run(
        topic=args.topic,
        num_rounds=args.rounds,
        verbose=True,
    )

    # Print detailed results
    if context.judge_score:
        print("\n" + "=" * 60)
        print("DETAILED RESULTS")
        print("=" * 60)

        print("\n--- Pro Arguments ---")
        for i, turn in enumerate(context.pro_turns, 1):
            print(f"\nRound {i}:")
            print(turn.argument[:300] + "..." if len(turn.argument) > 300 else turn.argument)

        print("\n--- Con Arguments ---")
        for i, turn in enumerate(context.con_turns, 1):
            print(f"\nRound {i}:")
            print(turn.argument[:300] + "..." if len(turn.argument) > 300 else turn.argument)

        print("\n--- Judgment ---")
        print(f"Pro Score: {context.judge_score.pro_score:.2f}/10")
        print(f"Con Score: {context.judge_score.con_score:.2f}/10")
        print(f"Winner: {context.judge_score.winner.upper()}")
        print(f"Reasoning: {context.judge_score.reasoning}")

        print("\n--- Metrics ---")
        if "fact_check" in context.metrics:
            print(f"Avg Faithfulness: {context.metrics['fact_check']['avg_faithfulness']:.3f}")

        if "artifacts" in context.metrics:
            print(f"\nArtifacts saved to:")
            for name, path in context.metrics["artifacts"].items():
                print(f"  {name}: {path}")

    print("\n✓ Debate complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
