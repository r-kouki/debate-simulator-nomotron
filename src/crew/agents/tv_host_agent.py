"""
TV Host Agent - Introduces and hosts the debate.

The TV host provides:
1. A welcoming introduction to the audience
2. Context and background on the topic
3. Framing of the key questions
4. Introduction of the debate format
"""

from dataclasses import dataclass
import re


@dataclass
class DebateIntroduction:
    """The TV host's debate introduction."""
    full_introduction: str


def generate_tv_host_introduction(
    topic: str,
    domain: str,
    research_summary: str = "",
    num_rounds: int = 2,
    model_manager = None,
) -> DebateIntroduction:
    """
    Generate a TV host introduction for the debate.
    
    Args:
        topic: The debate topic
        domain: Topic domain (economics, politics, etc.)
        research_summary: Brief research context
        num_rounds: Number of debate rounds
        model_manager: Optional model manager for LLM generation
        
    Returns:
        DebateIntroduction with the introduction text
    """
    # If model manager provided, use LLM to generate
    if model_manager:
        return _generate_with_llm(topic, domain, research_summary, num_rounds, model_manager)
    
    # Otherwise use template-based generation
    return _generate_template(topic, domain, research_summary, num_rounds)


def _generate_template(
    topic: str,
    domain: str,
    research_summary: str,
    num_rounds: int,
) -> DebateIntroduction:
    """Generate introduction using templates."""
    
    # Domain-specific openings
    domain_intros = {
        "economics": "Tonight, we dive into a topic that affects every wallet and household.",
        "politics": "In the arena of public policy, few topics generate as much debate.",
        "environment": "As our planet faces unprecedented challenges, this question is urgent.",
        "technology": "In an era of rapid technological change, we grapple with difficult questions.",
        "healthcare": "When it comes to our health and wellbeing, the stakes couldn't be higher.",
        "education": "The future of our children and society hangs in the balance.",
        "energy": "As the world seeks sustainable solutions, this debate is crucial.",
        "general": "Welcome to tonight's debate on a topic that matters to all of us.",
    }
    
    opening = domain_intros.get(domain.lower(), domain_intros["general"])
    
    full_intro = f"""Good evening and welcome!

{opening}

Our topic tonight: {topic}

Tonight's format: We'll have {num_rounds} rounds of debate where each side will present their arguments, respond to their opponent, and make their case to you, our audience.

Let the debate begin!"""
    
    return DebateIntroduction(full_introduction=full_intro)


def _generate_with_llm(
    topic: str,
    domain: str,
    research_summary: str,
    num_rounds: int,
    model_manager,
) -> DebateIntroduction:
    """Generate introduction using LLM."""
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a professional TV debate host. Write a brief, engaging introduction for tonight's debate.

Rules:
- Be professional but warm
- Stay neutral - don't take sides
- Keep it to 3-4 short paragraphs
- Welcome the audience, introduce the topic, explain the format
- NO meta-commentary, just the introduction itself<|eot_id|><|start_header_id|>user<|end_header_id|>

Debate topic: "{topic}"
Domain: {domain}
Rounds: {num_rounds}

Write the TV host introduction:<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    try:
        raw_intro = model_manager.generate_pro(prompt, max_tokens=300, temperature=0.7)
        intro_text = _clean_host_output(raw_intro)
        return DebateIntroduction(full_introduction=intro_text)
    except Exception as e:
        print(f"  ⚠ LLM introduction failed: {e}, using template")
        return _generate_template(topic, domain, research_summary, num_rounds)


def _clean_host_output(text: str) -> str:
    """Clean the host's generated introduction."""
    if not text:
        return ""
    
    # Remove markdown
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    
    # Remove meta-commentary
    text = re.sub(r'Here is (?:the |my |a )?introduction.*?:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Introduction:', '', text, flags=re.IGNORECASE)
    
    return text.strip()
