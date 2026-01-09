"""
Teacher Crew - CrewAI orchestration for educational content.

Provides structured lessons on any topic using:
1. Wikipedia for factual grounding
2. Internet research for current information
3. LLM for lesson generation and structuring
"""

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from src.crew.utils.dual_model_manager import DualModelManager
from src.crew.tools.internet_research import InternetResearchTool
from src.crew.tools.wikipedia_tool import WikipediaSearchTool
from src.crew.agents.teacher_agent import (
    create_teacher_agent,
    generate_lesson_prompt,
    parse_lesson_response,
    Lesson,
)
from src.crew.agents.router_agent import classify_domain


@dataclass
class TeachingSession:
    """Result of a teaching session."""
    topic: str
    domain: str
    lesson: Lesson
    research_context: str
    duration_seconds: float
    use_internet: bool


class TeacherCrew:
    """
    CrewAI-based teaching orchestration.
    
    Generates structured educational content using research tools
    and domain-specific model adapters.
    
    Separate from DebateCrew - focuses on education, not argumentation.
    """
    
    def __init__(
        self,
        use_internet: bool = True,
        output_dir: Path = None,
        verbose: bool = True,
    ):
        """
        Initialize the teacher crew.
        
        Args:
            use_internet: Enable internet research (default True for teaching)
            output_dir: Directory for saving lesson artifacts
            verbose: Print progress messages
        """
        self.use_internet = use_internet
        self.output_dir = output_dir or Path("runs/lessons")
        self.verbose = verbose
        
        # Initialize model manager (lazy loaded, uses only one instance)
        self._model_manager: Optional[DualModelManager] = None
        
        # Initialize tools
        self.internet_tool = InternetResearchTool(use_internet=use_internet)
        self.wikipedia_tool = WikipediaSearchTool()
        
        # Create teacher agent
        self.teacher = create_teacher_agent(
            internet_tool=self.internet_tool,
            wikipedia_tool=self.wikipedia_tool,
        )
    
    @property
    def model_manager(self) -> DualModelManager:
        """Lazy load model manager (uses Pro model for teaching)."""
        if self._model_manager is None:
            if self.verbose:
                print("Initializing model for teaching...")
            self._model_manager = DualModelManager()
        return self._model_manager
    
    def teach(
        self,
        topic: str,
        detail_level: str = "intermediate",
    ) -> TeachingSession:
        """
        Generate an educational lesson on a topic.
        
        Args:
            topic: The topic to teach
            detail_level: "beginner", "intermediate", or "advanced"
            
        Returns:
            TeachingSession with structured lesson
        """
        start_time = datetime.now()
        
        if self.verbose:
            print("=" * 60)
            print("CREWAI TEACHER")
            print("=" * 60)
            print(f"Topic: {topic}")
            print(f"Level: {detail_level}")
            print(f"Internet: {'Enabled' if self.use_internet else 'Disabled'}")
            print()
        
        # Clear caches
        self.internet_tool.clear_cache()
        self.wikipedia_tool.clear_cache()
        
        # Step 1: Classify domain for adapter selection
        if self.verbose:
            print("[1/4] Classifying topic domain...")
        domain, confidence = classify_domain(topic)
        if self.verbose:
            print(f"  → Domain: {domain} (confidence: {confidence:.2f})")
        
        # Step 2: Gather research
        if self.verbose:
            print("[2/4] Researching topic...")
        research_context = self._gather_research(topic)
        if self.verbose:
            print(f"  → Gathered {len(research_context)} chars of context")
        
        # Step 3: Load appropriate adapter
        if self.verbose:
            print("[3/4] Loading domain knowledge...")
        # Use education adapter by default for teaching, or domain-specific if available
        adapter_loaded = self.model_manager.load_adapter("pro", "education")
        if not adapter_loaded and domain != "debate":
            self.model_manager.load_adapter("pro", domain)
        
        # Step 4: Generate lesson
        if self.verbose:
            print("[4/4] Generating lesson...")
        lesson = self._generate_lesson(topic, research_context, detail_level)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Build result
        result = TeachingSession(
            topic=topic,
            domain=domain,
            lesson=lesson,
            research_context=research_context,
            duration_seconds=duration,
            use_internet=self.use_internet,
        )
        
        # Save lesson
        self._save_lesson(result)
        
        if self.verbose:
            print()
            print("=" * 60)
            print("LESSON GENERATED")
            print("=" * 60)
            print(f"Duration: {duration:.1f}s")
            self._print_lesson(lesson)
        
        return result
    
    def _gather_research(self, topic: str) -> str:
        """Gather educational research on the topic."""
        research_parts = []
        
        # Wikipedia - primary source for teaching
        try:
            # Get summary
            wiki_summary = self.wikipedia_tool._run(
                topic, search_type="summary", sentences=8
            )
            research_parts.append(f"WIKIPEDIA OVERVIEW:\n{wiki_summary}")
            
            # Get more detailed content
            wiki_full = self.wikipedia_tool._run(
                topic, search_type="full"
            )
            research_parts.append(f"DETAILED CONTENT:\n{wiki_full}")
        except Exception as e:
            if self.verbose:
                print(f"  ⚠ Wikipedia search failed: {e}")
        
        # Internet research for current perspectives
        if self.use_internet:
            try:
                internet_result = self.internet_tool._run(
                    topic, search_type="general"
                )
                research_parts.append(f"ADDITIONAL SOURCES:\n{internet_result}")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠ Internet search failed: {e}")
        
        return "\n\n".join(research_parts)
    
    def _generate_lesson(
        self,
        topic: str,
        research_context: str,
        detail_level: str,
    ) -> Lesson:
        """Generate a structured lesson using the LLM."""
        # Build prompt
        prompt = generate_lesson_prompt(topic, research_context, detail_level)
        
        # Generate using Pro model (education adapter loaded)
        response = self.model_manager.generate_pro(
            prompt,
            max_tokens=800,  # Lessons need more space
            temperature=0.7,
        )
        
        # Parse into structured lesson
        lesson = parse_lesson_response(response, topic)
        
        return lesson
    
    def _print_lesson(self, lesson: Lesson):
        """Print lesson in readable format."""
        print(f"\n## {lesson.topic}\n")
        
        print("### Overview")
        print(lesson.overview[:500] + "..." if len(lesson.overview) > 500 else lesson.overview)
        print()
        
        if lesson.key_concepts:
            print("### Key Concepts")
            for concept in lesson.key_concepts:
                print(f"  • {concept[:100]}")
            print()
        
        if lesson.examples:
            print("### Examples")
            for example in lesson.examples:
                print(f"  • {example[:100]}")
            print()
        
        if lesson.quiz_questions:
            print("### Review Questions")
            for i, q in enumerate(lesson.quiz_questions, 1):
                print(f"  {i}. {q}")
    
    def _save_lesson(self, session: TeachingSession):
        """Save lesson artifacts to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = "".join(c if c.isalnum() else "_" for c in session.topic[:30])
        
        lesson_dir = self.output_dir / f"{timestamp}_{topic_slug}"
        lesson_dir.mkdir(parents=True, exist_ok=True)
        
        # Save formatted lesson
        lesson_path = lesson_dir / "lesson.md"
        with open(lesson_path, "w") as f:
            f.write(f"# {session.lesson.topic}\n\n")
            f.write(f"*Generated: {timestamp}*\n")
            f.write(f"*Domain: {session.domain}*\n\n")
            
            f.write("## Overview\n\n")
            f.write(session.lesson.overview + "\n\n")
            
            if session.lesson.key_concepts:
                f.write("## Key Concepts\n\n")
                for concept in session.lesson.key_concepts:
                    f.write(f"- {concept}\n")
                f.write("\n")
            
            if session.lesson.examples:
                f.write("## Examples\n\n")
                for example in session.lesson.examples:
                    f.write(f"- {example}\n")
                f.write("\n")
            
            if session.lesson.further_reading:
                f.write("## Further Reading\n\n")
                for item in session.lesson.further_reading:
                    f.write(f"- {item['title']}\n")
                f.write("\n")
            
            if session.lesson.quiz_questions:
                f.write("## Review Questions\n\n")
                for i, q in enumerate(session.lesson.quiz_questions, 1):
                    f.write(f"{i}. {q}\n")
        
        # Save JSON
        import json
        json_path = lesson_dir / "lesson.json"
        with open(json_path, "w") as f:
            json.dump({
                "topic": session.topic,
                "domain": session.domain,
                "lesson": {
                    "overview": session.lesson.overview,
                    "key_concepts": session.lesson.key_concepts,
                    "examples": session.lesson.examples,
                    "further_reading": session.lesson.further_reading,
                    "quiz_questions": session.lesson.quiz_questions,
                },
                "duration_seconds": session.duration_seconds,
                "use_internet": session.use_internet,
            }, f, indent=2)
        
        if self.verbose:
            print(f"  → Saved to {lesson_dir}")
    
    def enable_internet(self):
        """Enable internet research."""
        self.use_internet = True
        self.internet_tool.enable_internet()
    
    def disable_internet(self):
        """Disable internet research."""
        self.use_internet = False
        self.internet_tool.disable_internet()
