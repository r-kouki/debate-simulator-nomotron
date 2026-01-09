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
        
        # Generate using appropriate model (increased tokens for structured rebuttals)
        if stance == "pro":
            argument = self._model_manager.generate_pro(
                prompt,
                max_tokens=450,  # Longer for Four-Step Refutation format
                temperature=0.7,
            )
        else:
            argument = self._model_manager.generate_con(
                prompt,
                max_tokens=450,
                temperature=0.7,
            )
        
        # Post-process to enforce sentence limit (increased for structured rebuttals)
        argument = self._enforce_sentence_limit(argument, max_sentences=12)
        
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
        
        # Check if this is an opening argument or a rebuttal
        is_opening = len(self._debate_history) == 0
        opponent = "CON" if stance == "pro" else "PRO"
        
        # Get opponent's last argument if available
        opponent_arg = self._get_opponent_last_argument(stance)
        
        # Simplified system message without example phrases
        if is_opening:
            system_msg = f"""You are an expert debater arguing {stance.upper()}.

Your task: Write a compelling opening argument.

Requirements:
- Start with a clear thesis statement
- Provide 2-3 strong supporting points with specific evidence
- Use facts, statistics, or real-world examples if available
- End with a strong conclusion
- Length: 8-12 sentences total
- Be specific and persuasive - avoid vague generalities"""
        else:
            system_msg = f"""You are an expert debater arguing {stance.upper()}.

Your task: Write a rebuttal that directly counters your opponent's argument.

Requirements:
- DIRECTLY address what {opponent} just argued - quote or paraphrase their specific points
- Explain WHY their reasoning or evidence is flawed
- Provide counter-evidence or new arguments that support YOUR side
- Length: 8-12 sentences
- Be specific - reference their actual claims, don't be generic
- After rebutting, add one NEW point for your side"""
        
        # Build research context
        research_section = ""
        if research_context:
            research_section = f"""
FACTS TO USE (cite these in your argument):
{research_context[:1200]}
"""
        
        # Build conversation history
        conversation_section = ""
        if self._debate_history:
            conversation_section = "\nPREVIOUS ARGUMENTS:\n"
            for turn in sorted(self._debate_history, key=lambda t: (t.round_num, t.timestamp)):
                side_label = "PRO" if turn.stance == "pro" else "CON"
                conversation_section += f"\n[{side_label} Round {turn.round_num}]:\n{turn.argument}\n"
        
        # Simplified instruction
        if is_opening:
            instruction = f"""Write your {stance.upper()} opening argument for the debate.

Topic: {topic}

Start your argument now:"""
        else:
            instruction = f"""Write your {stance.upper()} rebuttal for Round {round_num}.

Topic: {topic}

Opponent's argument to counter:
{opponent_arg if opponent_arg else 'No opponent argument yet.'}

Write your rebuttal now (directly address their points, then add your own):"""
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>
{research_section}{conversation_section}
{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    def _format_conversation(self) -> str:
        """Format debate history as a clear back-and-forth conversation."""
        if not self._debate_history:
            return "\n[This is the opening argument - no prior arguments to respond to]"
        
        lines = ["\n--- DEBATE CONVERSATION SO FAR ---"]
        lines.append("(You must respond to these points, especially the most recent one)\n")
        
        # Sort history by round and timestamp to ensure correct order
        sorted_history = sorted(self._debate_history, key=lambda t: (t.round_num, t.timestamp))
        
        for turn in sorted_history:
            stance_label = "PRO" if turn.stance == "pro" else "CON"
            marker = "🟢" if turn.stance == "pro" else "🔴"
            lines.append(f"{marker} [{stance_label} - Round {turn.round_num}]:")
            lines.append(f"   {turn.argument}")
            lines.append("")  # Empty line between turns
        
        lines.append("--- END OF CONVERSATION ---")
        lines.append("YOUR TURN: Respond to the above, especially the most recent argument.")
        
        return "\n".join(lines)
    
    def _format_history(self) -> str:
        """Format debate history for prompt context (legacy method)."""
        if not self._debate_history:
            return ""
        
        lines = ["\nDEBATE HISTORY (DO NOT repeat these points):"]
        for turn in self._debate_history[-6:]:  # Last 6 turns (3 rounds)
            stance_label = "PRO" if turn.stance == "pro" else "CON"
            lines.append(f"[Round {turn.round_num} - {stance_label}]: {turn.argument}")
        
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
