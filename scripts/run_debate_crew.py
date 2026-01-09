#!/usr/bin/env python3
"""
Run debate using CrewAI orchestration with dual model instances.

Usage:
    python scripts/run_debate_crew.py "Should AI be regulated?" --rounds 2
    python scripts/run_debate_crew.py "Is remote work better?" --rounds 3 --use-internet
    python scripts/run_debate_crew.py "Climate change solutions" --recommend-guests
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Run a CrewAI-powered debate simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Should college be free?"
  %(prog)s "Is AI a threat?" --rounds 3
  %(prog)s "Nuclear energy" --use-internet --recommend-guests
        """,
    )
    
    parser.add_argument(
        "topic",
        help="The debate topic",
    )
    parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=2,
        help="Number of debate rounds (default: 2)",
    )
    parser.add_argument(
        "--use-internet", "-i",
        action="store_true",
        help="Enable internet research for evidence gathering",
    )
    parser.add_argument(
        "--recommend-guests", "-g",
        action="store_true",
        help="Recommend real-world debate guests after the debate",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("runs/debates"),
        help="Directory to save debate artifacts (default: runs/debates)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce output verbosity",
    )
    
    args = parser.parse_args()
    
    # Import here to avoid slow startup for --help
    from src.crew.debate_crew import DebateCrew
    
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           CREWAI DEBATE SIMULATOR                        ║")
    print("║           Dual Model • Dynamic Adapters                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize crew
    crew = DebateCrew(
        use_internet=args.use_internet,
        output_dir=args.output_dir,
        verbose=not args.quiet,
    )
    
    # Run debate
    result = crew.run_debate(
        topic=args.topic,
        num_rounds=args.rounds,
        recommend_guests=args.recommend_guests,
    )
    
    # Print final summary
    print()
    print("━" * 60)
    print("FINAL RESULT")
    print("━" * 60)
    print(f"Topic: {result.topic}")
    print(f"Domain: {result.domain}")
    print(f"Rounds: {result.rounds}")
    print()
    
    print("PRO ARGUMENTS:")
    for i, arg in enumerate(result.pro_arguments, 1):
        print(f"  Round {i}: {arg[:150]}...")
    print()
    
    print("CON ARGUMENTS:")
    for i, arg in enumerate(result.con_arguments, 1):
        print(f"  Round {i}: {arg[:150]}...")
    print()
    
    print("VERDICT:")
    print(f"  Winner: {result.judge_score.winner.upper()}")
    print(f"  Pro Score: {result.judge_score.pro_score}")
    print(f"  Con Score: {result.judge_score.con_score}")
    print(f"  {result.judge_score.reasoning}")
    print()
    
    if result.recommended_guests:
        print("RECOMMENDED DEBATE GUESTS:")
        for guest in result.recommended_guests:
            print(f"  • {guest.name}")
            print(f"    {guest.credentials} | Likely stance: {guest.known_stance}")
        print()
    
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Internet: {'Enabled' if result.use_internet else 'Disabled'}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
