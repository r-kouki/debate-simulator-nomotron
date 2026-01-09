"""
Debate Crew - CrewAI orchestration for multi-agent debates.

Coordinates all debate agents in a structured workflow:
1. Domain routing
2. Research (with optional internet)
3. Alternating Pro/Con debate rounds
4. Fact-checking
5. Judging
6. Persona recommendations (optional)
"""

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from crewai import Crew, Task, Process

from src.crew.utils.dual_model_manager import DualModelManager
from src.crew.tools.internet_research import InternetResearchTool
from src.crew.tools.wikipedia_tool import WikipediaSearchTool
from src.crew.tools.debate_tool import DebateGenerationTool, DebateTurn

from src.crew.agents.router_agent import create_router_agent, classify_domain
from src.crew.agents.research_agent import create_research_agent
from src.crew.agents.debater_agents import create_pro_debater_agent, create_con_debater_agent
from src.crew.agents.factcheck_agent import create_factcheck_agent, compute_faithfulness_score
from src.crew.agents.judge_agent import create_judge_agent, judge_debate, JudgeScore
from src.crew.agents.persona_agent import create_persona_agent, recommend_debate_guests, DebateGuest


@dataclass
class DebateResult:
    """Complete debate result."""
    topic: str
    domain: str
    rounds: int
    pro_arguments: list[str] = field(default_factory=list)
    con_arguments: list[str] = field(default_factory=list)
    research_context: str = ""
    fact_check: dict = field(default_factory=dict)
    judge_score: Optional[JudgeScore] = None
    recommended_guests: list[DebateGuest] = field(default_factory=list)
    duration_seconds: float = 0.0
    use_internet: bool = False


class DebateCrew:
    """
    CrewAI-based debate orchestration with dual model instances.
    
    Features:
    - Dual model loading for Pro/Con parallel generation
    - Dynamic domain adapter loading
    - Per-session cached internet research
    - Wikipedia integration for persona recommendations
    - History-aware argument generation with 5-8 sentence limit
    """
    
    def __init__(
        self,
        use_internet: bool = False,
        output_dir: Path = None,
        verbose: bool = True,
    ):
        """
        Initialize the debate crew.
        
        Args:
            use_internet: Enable internet research (default False)
            output_dir: Directory for saving debate artifacts
            verbose: Print progress messages
        """
        self.use_internet = use_internet
        self.output_dir = output_dir or Path("runs/debates")
        self.verbose = verbose
        
        # Initialize model manager (lazy loaded)
        self._model_manager: Optional[DualModelManager] = None
        
        # Initialize shared tools
        self.internet_tool = InternetResearchTool(use_internet=use_internet)
        self.wikipedia_tool = WikipediaSearchTool()
        
        # Debate tools (initialized per debate with model manager)
        self._debate_tool_pro: Optional[DebateGenerationTool] = None
        self._debate_tool_con: Optional[DebateGenerationTool] = None
        
        # Create agents (some need tools injected)
        self.router = create_router_agent()
        self.researcher = create_research_agent(
            use_internet=use_internet,
            internet_tool=self.internet_tool,
            wikipedia_tool=self.wikipedia_tool,
        )
        self.factchecker = create_factcheck_agent()
        self.judge = create_judge_agent()
        self.persona_agent = create_persona_agent(
            internet_tool=self.internet_tool,
            wikipedia_tool=self.wikipedia_tool,
        )
    
    @property
    def model_manager(self) -> DualModelManager:
        """Lazy load the dual model manager."""
        if self._model_manager is None:
            if self.verbose:
                print("Initializing dual model manager...")
            self._model_manager = DualModelManager()
        return self._model_manager
    
    def _init_debate_tools(self):
        """Initialize debate generation tools with model manager."""
        if self._debate_tool_pro is None:
            self._debate_tool_pro = DebateGenerationTool(self.model_manager)
        if self._debate_tool_con is None:
            self._debate_tool_con = DebateGenerationTool(self.model_manager)
    
    def run_debate(
        self,
        topic: str,
        num_rounds: int = 2,
        recommend_guests: bool = False,
    ) -> DebateResult:
        """
        Run a complete debate on the given topic.
        
        Args:
            topic: The debate topic
            num_rounds: Number of Pro/Con exchange rounds
            recommend_guests: Whether to recommend real debate guests
            
        Returns:
            DebateResult with all debate data
        """
        start_time = datetime.now()
        
        if self.verbose:
            print("=" * 60)
            print("CREWAI DEBATE SIMULATOR")
            print("=" * 60)
            print(f"Topic: {topic}")
            print(f"Rounds: {num_rounds}")
            print(f"Internet: {'Enabled' if self.use_internet else 'Disabled'}")
            print()
        
        # Initialize tools
        self._init_debate_tools()
        self._debate_tool_pro.clear_history()
        self._debate_tool_con.clear_history()
        
        # Clear caches for new session
        self.internet_tool.clear_cache()
        self.wikipedia_tool.clear_cache()
        
        # Step 1: Route domain
        if self.verbose:
            print("[1/6] Routing domain...")
        domain, confidence = classify_domain(topic)
        if self.verbose:
            print(f"  → Domain: {domain} (confidence: {confidence:.2f})")
        
        # Step 2: Research
        if self.verbose:
            print("[2/6] Gathering research...")
        research_context = self._gather_research(topic)
        if self.verbose:
            print(f"  → Research gathered ({len(research_context)} chars)")
        
        # Step 3: Debate rounds
        if self.verbose:
            print(f"[3/6] Running {num_rounds} debate rounds...")
        
        pro_arguments = []
        con_arguments = []
        
        for round_num in range(1, num_rounds + 1):
            if self.verbose:
                print(f"  Round {round_num}:")
            
            # Pro argument
            pro_arg = self._generate_argument(
                topic=topic,
                domain=domain,
                stance="pro",
                research_context=research_context,
                round_num=round_num,
            )
            pro_arguments.append(pro_arg)
            if self.verbose:
                print(f"    PRO: {pro_arg[:100]}...")
            
            # Record pro argument in con's history for awareness
            self._debate_tool_con.add_external_turn("pro", pro_arg, round_num)
            
            # Con argument
            con_arg = self._generate_argument(
                topic=topic,
                domain=domain,
                stance="con",
                research_context=research_context,
                round_num=round_num,
            )
            con_arguments.append(con_arg)
            if self.verbose:
                print(f"    CON: {con_arg[:100]}...")
            
            # Record con argument in pro's history
            self._debate_tool_pro.add_external_turn("con", con_arg, round_num)
        
        # Step 4: Fact-check
        if self.verbose:
            print("[4/6] Fact-checking arguments...")
        fact_check = self._fact_check_debate(
            pro_arguments, con_arguments, research_context
        )
        if self.verbose:
            print(f"  → Pro faithfulness: {fact_check['pro']['faithfulness_score']:.2f}")
            print(f"  → Con faithfulness: {fact_check['con']['faithfulness_score']:.2f}")
        
        # Step 5: Judge
        if self.verbose:
            print("[5/6] Judging debate...")
        judge_score = judge_debate(pro_arguments, con_arguments, fact_check)
        if self.verbose:
            print(f"  → Winner: {judge_score.winner.upper()}")
            print(f"  → Pro score: {judge_score.pro_score}, Con score: {judge_score.con_score}")
        
        # Step 6: Persona recommendations (optional)
        recommended_guests = []
        if recommend_guests:
            if self.verbose:
                print("[6/6] Finding debate guests...")
            recommended_guests = recommend_debate_guests(
                topic=topic,
                domain=domain,
                wikipedia_tool=self.wikipedia_tool,
                internet_tool=self.internet_tool if self.use_internet else None,
                num_guests=4,
            )
            if self.verbose:
                print(f"  → Found {len(recommended_guests)} potential guests")
                for guest in recommended_guests:
                    print(f"    - {guest.name} ({guest.credentials})")
        else:
            if self.verbose:
                print("[6/6] Skipping guest recommendations")
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Build result
        result = DebateResult(
            topic=topic,
            domain=domain,
            rounds=num_rounds,
            pro_arguments=pro_arguments,
            con_arguments=con_arguments,
            research_context=research_context,
            fact_check=fact_check,
            judge_score=judge_score,
            recommended_guests=recommended_guests,
            duration_seconds=duration,
            use_internet=self.use_internet,
        )
        
        # Save artifacts
        self._save_debate(result)
        
        if self.verbose:
            print()
            print("=" * 60)
            print("DEBATE COMPLETE")
            print("=" * 60)
            print(f"Duration: {duration:.1f}s")
            print(f"Result: {result.judge_score.reasoning}")
        
        return result
    
    def _gather_research(self, topic: str) -> str:
        """Gather research context using available tools."""
        research_parts = []
        
        # Wikipedia summary
        try:
            wiki_result = self.wikipedia_tool._run(topic, search_type="summary", sentences=5)
            research_parts.append(f"WIKIPEDIA:\n{wiki_result}")
        except Exception as e:
            if self.verbose:
                print(f"  ⚠ Wikipedia search failed: {e}")
        
        # Internet research (if enabled)
        if self.use_internet:
            try:
                internet_result = self.internet_tool._run(topic, search_type="debate")
                research_parts.append(f"WEB RESEARCH:\n{internet_result}")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠ Internet search failed: {e}")
        
        return "\n\n".join(research_parts)
    
    def _generate_argument(
        self,
        topic: str,
        domain: str,
        stance: str,
        research_context: str,
        round_num: int,
    ) -> str:
        """Generate a debate argument."""
        tool = self._debate_tool_pro if stance == "pro" else self._debate_tool_con
        
        return tool._run(
            topic=topic,
            domain=domain,
            stance=stance,
            research_context=research_context,
            round_num=round_num,
        )
    
    def _fact_check_debate(
        self,
        pro_arguments: list[str],
        con_arguments: list[str],
        research_context: str,
    ) -> dict:
        """Fact-check all debate arguments."""
        pro_combined = " ".join(pro_arguments)
        con_combined = " ".join(con_arguments)
        
        return {
            "pro": compute_faithfulness_score(pro_combined, research_context),
            "con": compute_faithfulness_score(con_combined, research_context),
        }
    
    def _save_debate(self, result: DebateResult):
        """Save debate artifacts to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = "".join(c if c.isalnum() else "_" for c in result.topic[:30])
        
        debate_dir = self.output_dir / f"{timestamp}_{topic_slug}"
        debate_dir.mkdir(parents=True, exist_ok=True)
        
        # Save transcript
        transcript_path = debate_dir / "transcript.txt"
        with open(transcript_path, "w") as f:
            f.write(f"DEBATE: {result.topic}\n")
            f.write(f"Domain: {result.domain}\n")
            f.write(f"Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, (pro, con) in enumerate(zip(result.pro_arguments, result.con_arguments), 1):
                f.write(f"--- ROUND {i} ---\n\n")
                f.write(f"PRO:\n{pro}\n\n")
                f.write(f"CON:\n{con}\n\n")
            
            f.write("=" * 60 + "\n")
            f.write(f"VERDICT: {result.judge_score.winner.upper()}\n")
            f.write(f"{result.judge_score.reasoning}\n")
            
            if result.recommended_guests:
                f.write("\n" + "=" * 60 + "\n")
                f.write("RECOMMENDED DEBATE GUESTS:\n")
                for guest in result.recommended_guests:
                    f.write(f"\n- {guest.name}\n")
                    f.write(f"  Credentials: {guest.credentials}\n")
                    f.write(f"  Likely stance: {guest.known_stance}\n")
        
        # Save JSON result
        import json
        result_path = debate_dir / "result.json"
        with open(result_path, "w") as f:
            json.dump({
                "topic": result.topic,
                "domain": result.domain,
                "rounds": result.rounds,
                "pro_arguments": result.pro_arguments,
                "con_arguments": result.con_arguments,
                "fact_check": result.fact_check,
                "judge": {
                    "pro_score": result.judge_score.pro_score,
                    "con_score": result.judge_score.con_score,
                    "winner": result.judge_score.winner,
                    "reasoning": result.judge_score.reasoning,
                },
                "recommended_guests": [
                    {
                        "name": g.name,
                        "credentials": g.credentials,
                        "stance": g.known_stance,
                        "bio": g.bio,
                        "url": g.source_url,
                    }
                    for g in result.recommended_guests
                ],
                "duration_seconds": result.duration_seconds,
                "use_internet": result.use_internet,
            }, f, indent=2)
        
        if self.verbose:
            print(f"  → Saved to {debate_dir}")
    
    def enable_internet(self):
        """Enable internet research."""
        self.use_internet = True
        self.internet_tool.enable_internet()
    
    def disable_internet(self):
        """Disable internet research."""
        self.use_internet = False
        self.internet_tool.disable_internet()
    
    def get_memory_stats(self) -> dict:
        """Get GPU memory statistics."""
        if self._model_manager:
            return self._model_manager.get_memory_stats()
        return {"models_loaded": False}
