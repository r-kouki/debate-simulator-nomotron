"""
Debate Generation Tool - Generate debate arguments with history awareness.

Uses the DualModelManager to generate arguments that:
- Consider full debate history
- Stay within 5-8 sentence limit
- Leverage domain-specific adapters
- Reference research context when relevant
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


@dataclass
class DebateTurn:
    """Represents a single turn in the debate."""
    stance: str  # "pro" or "con"
    argument: str
    round_num: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DebateGenerationInput(BaseModel):
    """Input schema for debate generation."""
    topic: str = Field(..., description="The debate topic")
    domain: str = Field(default="debate", description="Domain category for adapter selection")
    stance: str = Field(..., description="Stance: 'pro' or 'con'")
    research_context: str = Field(default="", description="Research findings to reference")
    round_num: int = Field(default=1, description="Current debate round number")


class DebateGenerationTool(BaseTool):
    """
    CrewAI tool for generating debate arguments.
    
    Features:
    - Full debate history awareness
    - 5-8 sentence response limit (system prompt enforced)
    - Domain adapter loading
    - Research context integration
    - Selective argument construction
    """
    
    name: str = "Generate Debate Argument"
    description: str = (
        "Generate a debate argument for a given stance. "
        "Arguments are concise (5 sentences, max 8 if critical) and "
        "consider previous arguments in the debate."
    )
    args_schema: type[BaseModel] = DebateGenerationInput
    
    # Will be set during initialization
    _model_manager = None
    _debate_history: list = None
    
    def __init__(self, model_manager, **kwargs):
        """
        Initialize the debate tool.
        
        Args:
            model_manager: DualModelManager instance for text generation
        """
        super().__init__(**kwargs)
        self._model_manager = model_manager
        self._debate_history = []
    
    def _run(
        self,
        topic: str,
        stance: str,
        domain: str = "debate",
        research_context: str = "",
        round_num: int = 1,
    ) -> str:
        """
        Generate a debate argument.
        
        Args:
            topic: Debate topic
            stance: "pro" or "con"
            domain: Domain for adapter (education, medicine, etc.)
            research_context: Research findings to reference
            round_num: Current round number
            
        Returns:
            Generated argument text
        """
        if stance not in ("pro", "con"):
            return f"Invalid stance: {stance}. Use 'pro' or 'con'."
        
        # Load appropriate adapter
        self._model_manager.load_adapter(stance, domain)
        
        # Build prompt with history and constraints
        prompt = self._build_prompt(topic, stance, research_context, round_num)
        
        # Generate using appropriate model
        if stance == "pro":
            argument = self._model_manager.generate_pro(
                prompt,
                max_tokens=250,  # ~8 sentences max
                temperature=0.7,
            )
        else:
            argument = self._model_manager.generate_con(
                prompt,
                max_tokens=250,
                temperature=0.7,
            )
        
        # Post-process to enforce sentence limit
        argument = self._enforce_sentence_limit(argument)
        
        # Record in history
        turn = DebateTurn(
            stance=stance,
            argument=argument,
            round_num=round_num,
        )
        self._debate_history.append(turn)
        
        return argument
    
    def _build_prompt(
        self,
        topic: str,
        stance: str,
        research_context: str,
        round_num: int,
    ) -> str:
        """Build the generation prompt with history and constraints."""
        
        # System message with strict length constraint
        system_msg = f"""You are an expert debater arguing the {stance.upper()} position.

CRITICAL RULES:
1. Respond in EXACTLY 5 sentences. Only use up to 8 sentences if the point is absolutely critical.
2. Be concise and impactful - every sentence must add value.
3. Reference specific evidence when available.
4. Address opponent's arguments directly when responding.
5. Maintain civil, professional tone."""

        # Build debate history section
        history_section = self._format_history()
        
        # Research context section
        research_section = ""
        if research_context:
            research_section = f"""
RESEARCH CONTEXT (use relevant points):
{research_context[:1000]}
"""
        
        # Opponent's last argument for direct response
        opponent_section = ""
        opponent_last = self._get_opponent_last_argument(stance)
        if opponent_last:
            opponent_section = f"""
OPPONENT'S LAST ARGUMENT (respond to this):
{opponent_last}
"""
        
        # Construct full prompt using Llama 3 format
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>

DEBATE TOPIC: {topic}
YOUR STANCE: {stance.upper()}
ROUND: {round_num}
{research_section}{history_section}{opponent_section}
Generate your {stance} argument now. Remember: 5 sentences (max 8 if critical).<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    def _format_history(self) -> str:
        """Format debate history for prompt context."""
        if not self._debate_history:
            return ""
        
        lines = ["\nDEBATE HISTORY:"]
        for turn in self._debate_history[-6:]:  # Last 6 turns (3 rounds)
            stance_label = "PRO" if turn.stance == "pro" else "CON"
            lines.append(f"[Round {turn.round_num} - {stance_label}]: {turn.argument[:300]}...")
        
        return "\n".join(lines)
    
    def _get_opponent_last_argument(self, current_stance: str) -> Optional[str]:
        """Get the opponent's most recent argument."""
        opponent_stance = "con" if current_stance == "pro" else "pro"
        
        for turn in reversed(self._debate_history):
            if turn.stance == opponent_stance:
                return turn.argument
        
        return None
    
    def _enforce_sentence_limit(self, text: str, max_sentences: int = 8) -> str:
        """
        Enforce sentence limit on generated text.
        
        Args:
            text: Generated text
            max_sentences: Maximum sentences allowed
            
        Returns:
            Truncated text if needed
        """
        # Simple sentence splitting (handles common cases)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        if len(sentences) <= max_sentences:
            return text
        
        # Keep only max_sentences
        truncated = " ".join(sentences[:max_sentences])
        
        # Ensure it ends with punctuation
        if not truncated.endswith((".", "!", "?")):
            truncated += "."
        
        return truncated
    
    def get_history(self) -> list[DebateTurn]:
        """Get the full debate history."""
        return self._debate_history.copy()
    
    def clear_history(self):
        """Clear debate history for a new debate."""
        self._debate_history.clear()
    
    def add_external_turn(self, stance: str, argument: str, round_num: int):
        """
        Add an externally generated turn to history.
        
        Useful for human-vs-AI debates where the human's turn
        needs to be recorded.
        """
        turn = DebateTurn(
            stance=stance,
            argument=argument,
            round_num=round_num,
        )
        self._debate_history.append(turn)
