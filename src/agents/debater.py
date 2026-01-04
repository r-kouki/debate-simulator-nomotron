"""
Debater Agent - Generates debate arguments using LLM with adapters.
"""

from pathlib import Path
import torch
from transformers import GenerationConfig
from peft import PeftModel

from src.agents.base import Agent, AgentState, DebateContext, DebateTurn
from src.utils.model_loader import load_base_model, ADAPTERS_PATH


class DebaterAgent(Agent):
    """
    Generates debate arguments for pro or con positions.

    Uses the base model with domain-specific LoRA adapters
    when available.
    """

    def __init__(
        self,
        stance: str,
        model=None,
        tokenizer=None,
        use_adapter: bool = True,
    ):
        """
        Initialize debater agent.

        Args:
            stance: "pro" or "con"
            model: Pre-loaded model (optional, will load if not provided)
            tokenizer: Pre-loaded tokenizer
            use_adapter: Whether to use domain adapters
        """
        super().__init__(f"Debater_{stance.upper()}")
        self.stance = stance.lower()
        self.use_adapter = use_adapter
        self._model = model
        self._tokenizer = tokenizer
        self._loaded_adapter = None

    def _ensure_model_loaded(self):
        """Load model if not already loaded."""
        if self._model is None:
            self._model, self._tokenizer = load_base_model()

    def _load_adapter(self, domain: str):
        """Load domain-specific adapter if available."""
        if not self.use_adapter:
            return

        if self._loaded_adapter == domain:
            return

        adapter_path = ADAPTERS_PATH / domain
        if adapter_path.exists():
            # Reload base model and apply adapter
            if isinstance(self._model, PeftModel):
                # Unload current adapter
                self._model = self._model.base_model.model

            self._model = PeftModel.from_pretrained(self._model, adapter_path)
            self._loaded_adapter = domain

    def _format_prompt(
        self,
        topic: str,
        domain: str,
        context: str,
        previous_arguments: list[str] | None = None,
    ) -> str:
        """Format the prompt for debate generation."""
        system_msg = f"""You are an expert debate assistant specializing in {domain}.
Generate compelling, well-reasoned arguments backed by evidence.
Be concise but thorough. Use logical reasoning and cite relevant facts."""

        previous_context = ""
        if previous_arguments:
            previous_context = "\n\nPrevious arguments in this debate:\n"
            for i, arg in enumerate(previous_arguments, 1):
                previous_context += f"{i}. {arg}\n"

        user_msg = f"""Topic: {topic}
Stance: {self.stance.upper()} ({"in favor" if self.stance == "pro" else "against"})

Background information:
{context}
{previous_context}
Generate a single, persuasive argument for this position. Focus on one main point with supporting reasoning."""

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt

    def _generate(
        self,
        prompt: str,
        max_new_tokens: int = 200,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from prompt."""
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=0.9,
            do_sample=True,
            pad_token_id=self._tokenizer.pad_token_id,
            eos_token_id=self._tokenizer.eos_token_id,
        )

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                generation_config=generation_config,
            )

        full_response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the assistant's response
        # Find the marker and take text after it
        marker = "Focus on one main point with supporting reasoning."
        if marker in full_response:
            response = full_response.split(marker)[-1].strip()
        else:
            # Fallback: take last portion after prompt length
            response = full_response[len(prompt):].strip()

        return response

    def generate_argument(
        self,
        topic: str,
        domain: str,
        retrieved_passages: list[dict],
        previous_arguments: list[str] | None = None,
    ) -> DebateTurn:
        """
        Generate a debate argument.

        Args:
            topic: Debate topic
            domain: Domain for adapter selection
            retrieved_passages: Context passages from research
            previous_arguments: Previous arguments in the debate

        Returns:
            DebateTurn with the generated argument
        """
        self._ensure_model_loaded()
        self._load_adapter(domain)

        # Build context from retrieved passages
        context = "\n".join(
            f"- {p['text']}" for p in retrieved_passages[:3]
        )

        prompt = self._format_prompt(topic, domain, context, previous_arguments)
        argument = self._generate(prompt)

        # Track which sources were used
        sources = [p["source"] for p in retrieved_passages[:3]]

        return DebateTurn(
            stance=self.stance,
            argument=argument,
            sources=sources,
        )

    def process(self, context: DebateContext) -> DebateContext:
        """Generate debate argument and update context."""
        self._log(context, "starting_generation", {
            "stance": self.stance,
            "round": context.current_round,
        })

        # Get previous arguments for context
        previous_args = []
        if self.stance == "con" and context.pro_turns:
            previous_args = [t.argument for t in context.pro_turns]
        elif self.stance == "pro" and context.con_turns:
            previous_args = [t.argument for t in context.con_turns]

        # Generate argument
        turn = self.generate_argument(
            topic=context.topic,
            domain=context.domain or "education",
            retrieved_passages=context.retrieved_passages,
            previous_arguments=previous_args,
        )

        # Add to appropriate list
        if self.stance == "pro":
            context.pro_turns.append(turn)
            context.current_state = AgentState.DEBATING_CON
        else:
            context.con_turns.append(turn)
            # After con, check if we need more rounds
            context.current_round += 1
            if context.current_round >= context.num_rounds:
                context.current_state = AgentState.FACT_CHECKING
            else:
                context.current_state = AgentState.DEBATING_PRO

        self._log(context, "generation_complete", {
            "argument_length": len(turn.argument),
            "sources_used": len(turn.sources),
        })

        return context
