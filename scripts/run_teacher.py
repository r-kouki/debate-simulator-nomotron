#!/usr/bin/env python3
"""
Run teacher mode for educational content generation.

Usage:
    python scripts/run_teacher.py "Quantum Computing"
    python scripts/run_teacher.py "Climate Change" --level beginner
    python scripts/run_teacher.py "Machine Learning" --level advanced --no-internet
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Generate educational lessons using CrewAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Photosynthesis"
  %(prog)s "Blockchain" --level beginner
  %(prog)s "Neural Networks" --level advanced
  %(prog)s "History of Rome" --no-internet
        """,
    )
    
    parser.add_argument(
        "topic",
        help="The topic to teach",
    )
    parser.add_argument(
        "--level", "-l",
        choices=["beginner", "intermediate", "advanced"],
        default="intermediate",
        help="Detail level for the lesson (default: intermediate)",
    )
    parser.add_argument(
        "--no-internet",
        action="store_true",
        help="Disable internet research (use Wikipedia and model knowledge only)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("runs/lessons"),
        help="Directory to save lesson artifacts (default: runs/lessons)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce output verbosity",
    )
    
    args = parser.parse_args()
    
    # Import here to avoid slow startup for --help
    from src.crew.teacher_crew import TeacherCrew
    
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           CREWAI TEACHER                                 ║")
    print("║           Learn Any Topic                                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize crew
    crew = TeacherCrew(
        use_internet=not args.no_internet,
        output_dir=args.output_dir,
        verbose=not args.quiet,
    )
    
    # Generate lesson
    result = crew.teach(
        topic=args.topic,
        detail_level=args.level,
    )
    
    # Print full lesson
    print()
    print("━" * 60)
    print("LESSON CONTENT")
    print("━" * 60)
    
    lesson = result.lesson
    
    print(f"\n# {lesson.topic}\n")
    
    print("## Overview\n")
    print(lesson.overview)
    print()
    
    if lesson.key_concepts:
        print("## Key Concepts\n")
        for i, concept in enumerate(lesson.key_concepts, 1):
            print(f"{i}. {concept}")
        print()
    
    if lesson.examples:
        print("## Examples\n")
        for i, example in enumerate(lesson.examples, 1):
            print(f"{i}. {example}")
        print()
    
    if lesson.further_reading:
        print("## Further Reading\n")
        for item in lesson.further_reading:
            print(f"• {item['title']}")
        print()
    
    if lesson.quiz_questions:
        print("## Review Questions\n")
        for i, q in enumerate(lesson.quiz_questions, 1):
            print(f"{i}. {q}")
        print()
    
    print("━" * 60)
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Domain: {result.domain}")
    print(f"Internet: {'Enabled' if result.use_internet else 'Disabled'}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
