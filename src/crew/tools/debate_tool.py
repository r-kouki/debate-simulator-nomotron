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
            Generated argument text (clean, single paragraph)
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
                max_tokens=450,
                temperature=0.7,
            )
        else:
            argument = self._model_manager.generate_con(
                prompt,
                max_tokens=450,
                temperature=0.7,
            )
        
        # Clean output: remove prompt artifacts and format as paragraph
        argument = self._clean_output(argument)
        
        # Post-process to enforce sentence limit
        argument = self._enforce_sentence_limit(argument, max_sentences=10)
        
        # Record in history
        turn = DebateTurn(
            stance=stance,
            argument=argument,
            round_num=round_num,
        )
        self._debate_history.append(turn)
        
        return argument
    
    def _clean_output(self, text: str) -> str:
        """
        Clean generated output by removing prompt artifacts and formatting as paragraph.
        
        Removes:
        - Markdown formatting (**, *, #, etc.)
        - Meta-commentary ("Here is a compelling argument...")
        - Research errors ("WIKIPEDIA: No Wikipedia page found")
        - Formatting artifacts
        
        Returns:
        - Clean, well-formatted single paragraph
        """
        import re
        
        if not text:
            return ""
        
        # FIRST: Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold **text**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic *text*
        text = re.sub(r'#{1,6}\s*', '', text)           # Headers # ## ###
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Inline code
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links [text](url)
        
        # Patterns to remove completely - comprehensive list
        remove_patterns = [
            # Meta-commentary about the argument (expanded)
            r'Here is (?:a |my |the )?(?:compelling |strong )?(?:opening )?(?:argument|statement|response).*?:',
            r'Here is (?:a |my |the )?(?:compelling |strong )?rebuttal.*?:',
            r'Opening Statement:?',
            r'Counter:?\s*',
            r'Specific Claim Addressed:?',
            r'My (?:opening )?(?:argument|statement):?',
            r'My response(?: as PRO| as CON)?:?',
            r'\(Word count:?\s*\d*\)',
            r'Word count:?\s*\d+',
            r'Note:?\s*',
            r'(?:incorporating|adhering to|following) the (?:given facts|critical style rules|style rules).*?:',
            
            # Remember blocks and instruction lists
            r'Remember:.*?(?=\n\n|\Z)',
            r'- Hook the audience.*?(?=\n|$)',
            r'- Make \d+-\d+ strong.*?(?=\n|$)',
            r'- Sound like.*?(?=\n|$)',
            r'- End memorably.*?(?=\n|$)',
            r'- Start (?:with|by).*?(?=\n|$)',
            
            # Topic and debate markers
            r'DEBATE TOPIC:.*?(?=\n\n|\n[A-Z])',
            r'Topic:.*?(?=\n)',
            
            # Research errors
            r'WIKIPEDIA:.*?(?=\.|$)\.?',
            r'Wikipedia:.*?(?=\.|$)\.?',
            r'No Wikipedia page.*?(?=\.|$)\.?',
            r'Research failed:.*?(?=\.|$)\.?',
            
            # Instructions
            r'Use these facts.*?(?=\n\n|\n[A-Z])',
            r'FACTS TO USE.*?(?=\n\n|\n[A-Z])',
            r'Your opening statement:?',
            r'Your response:?',
            r'Write a compelling.*?(?=\n|$)',
            r'Now COUNTER.*?(?=\n|$)',
            
            # Conversation markers
            r'--- What\'s been said.*?---',
            r'--- End of previous.*?---',
            r'\[PRO\]:.*?(?=\n\n|\n\[)',
            r'\[CON\]:.*?(?=\n\n|\n\[)',
            r'The other side just argued:.*?(?=\n\n)',
            
            # Quoted opponent's full argument
            r'"[^"]{150,}"',
        ]
        
        for pattern in remove_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove orphaned asterisks and other artifacts
        text = re.sub(r'\s*\*+\s*', ' ', text)  # Orphan asterisks
        text = re.sub(r'^[\-\*•]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Clean up whitespace
        text = re.sub(r'\n{2,}', ' ', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Remove leading/trailing whitespace and punctuation artifacts
        text = text.strip()
        text = re.sub(r'^[\'":\s\*]+', '', text)
        
        # Find where the actual argument starts (capital letter followed by lowercase)
        match = re.search(r'[A-Z][a-z]', text)
        if match and match.start() > 0 and match.start() < 20:
            text = text[match.start():]
        
        return text.strip()
    
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
        my_side = stance.upper()
        
        # Get opponent's last argument if available
        opponent_arg = self._get_opponent_last_argument(stance)
        
        # Natural, conversational system message
        if is_opening:
            system_msg = f"""You are a passionate, articulate debater in a live public debate. Your goal is to WIN the audience to YOUR side.

CRITICAL STYLE RULES:
- Speak naturally like a confident human advocate, NOT like a robot or ChatGPT
- NEVER start with "I will argue..." or "In this argument..." or similar academic phrases  
- NEVER say "my opponent" - refer to them as "those who disagree" or "critics" or "the other side"
- START with a powerful hook: a question, a striking fact, or a bold claim
- Use rhetorical questions to engage the audience
- Include ONE vivid real-world example or analogy
- Show genuine emotion and conviction - you BELIEVE in your position
- End with a memorable, quotable line

Your side: {my_side} (arguing IN FAVOR of the topic)
Length: 6-10 sentences, no more."""
        else:
            system_msg = f"""You are a passionate debater responding to your opponent in a live debate. Your goal is to DEMOLISH their argument while strengthening your own position.

CRITICAL STYLE RULES:
- Speak naturally like a confident human advocate, NOT like a robot
- NEVER start with "The opponent argues..." or "In response to..." - these are boring!
- START by directly quoting or paraphrasing ONE specific claim they made, then attack it
- Use phrases like "Really?", "Let's examine that claim", "Here's what they're missing"
- Point out logical flaws, missing context, or cherry-picked facts
- Provide counter-evidence or a better interpretation
- Add ONE new point for your side that they haven't addressed
- Show passion - be firm but not rude
- End with a powerful statement that reframes the debate

Your side: {my_side}
Length: 6-10 sentences, no more."""
        
        # Build research context (simplified, usable format)
        research_section = ""
        if research_context:
            # Extract just the key facts, not the formatting
            clean_research = research_context.replace("##", "").replace("**", "")
            research_section = f"""
Use these facts to strengthen your argument (cite specifics!):
{clean_research[:1000]}
"""
        
        # Build conversation history in a natural way
        conversation_section = ""
        if self._debate_history:
            conversation_section = "\n--- What's been said so far ---\n"
            for turn in sorted(self._debate_history, key=lambda t: (t.round_num, t.timestamp)):
                side_label = "PRO" if turn.stance == "pro" else "CON"
                conversation_section += f"\n[{side_label}]: {turn.argument}\n"
            conversation_section += "--- End of previous arguments ---\n"
        
        # Natural instruction without academic framing
        if is_opening:
            instruction = f"""DEBATE TOPIC: {topic}

Write a compelling opening argument for the {my_side} side. Remember:
- Hook the audience immediately
- Make 2-3 strong points with evidence
- Sound like a passionate human advocate, not a textbook
- End memorably

Your opening statement:"""
        else:
            instruction = f"""DEBATE TOPIC: {topic}

The other side just argued:
"{opponent_arg[:400] if opponent_arg else 'No previous argument'}"

Now COUNTER their argument and advance YOUR position ({my_side}). Remember:
- Start by addressing their specific claim
- Show why they're wrong or missing the point
- Add fresh evidence or arguments
- Sound passionate and human

Your response:"""
        
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
