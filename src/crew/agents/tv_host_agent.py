"""
TV Host Agent - Introduces and hosts the debate.

The TV host provides:
1. A welcoming introduction to the audience
2. Context and background on the topic
3. Framing of the key questions
4. Introduction of the debate format
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class DebateIntroduction:
    """The TV host's debate introduction."""
    opening: str
    topic_context: str
    key_questions: list[str]
    format_explanation: str
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
        DebateIntroduction with all components
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
        "economics": "Tonight, we dive into a topic that affects every wallet and every household.",
        "politics": "In the arena of public policy, few topics generate as much debate.",
        "environment": "As our planet faces unprecedented challenges, this question has never been more urgent.",
        "technology": "In an era of rapid technological change, we must grapple with difficult questions.",
        "healthcare": "When it comes to our health and wellbeing, the stakes couldn't be higher.",
        "education": "The future of our children and our society hangs in the balance.",
        "energy": "As the world seeks sustainable solutions, this debate is at the heart of our future.",
        "general": "Welcome to tonight's debate on a topic that matters deeply to all of us.",
    }
    
    opening = domain_intros.get(domain.lower(), domain_intros["general"])
    
    # Topic context
    topic_context = f"Our topic tonight: **{topic}**. "
    if research_summary:
        # Extract a brief context from research
        context_snippet = research_summary[:200].replace('\n', ' ').strip()
        if context_snippet:
            topic_context += f"This debate touches on key issues including {context_snippet}..."
    else:
        topic_context += "This is a topic that has sparked passionate discussion on all sides."
    
    # Key questions
    key_questions = [
        f"What are the real benefits and risks of {topic.lower()}?",
        "Who stands to gain, and who might be left behind?",
        "What does the evidence actually tell us?",
    ]
    
    # Format explanation
    format_explanation = (
        f"Tonight's format: We'll have {num_rounds} rounds of debate. "
        f"Each side will present their arguments, respond to their opponent, "
        f"and make their case to you, our audience. "
        f"Let the debate begin!"
    )
    
    # Combine into full introduction
    full_intro = f"""Good evening and welcome!

{opening}

{topic_context}

Tonight, our debaters will tackle questions such as:
• {key_questions[0]}
• {key_questions[1]}
• {key_questions[2]}

{format_explanation}"""
    
    return DebateIntroduction(
        opening=opening,
        topic_context=topic_context,
        key_questions=key_questions,
        format_explanation=format_explanation,
        full_introduction=full_intro,
    )


def _generate_with_llm(
    topic: str,
    domain: str,
    research_summary: str,
    num_rounds: int,
    model_manager,
) -> DebateIntroduction:
    """Generate introduction using LLM."""
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a professional TV debate host. Your job is to introduce tonight's debate topic in an engaging, neutral way.

Style:
- Professional but warm and engaging
- Neutral - don't take sides
- Build anticipation and interest
- Keep it concise (3-4 short paragraphs max)

Do NOT include any instructions or meta-commentary. Just write the introduction directly.<|eot_id|><|start_header_id|>user<|end_header_id|>

Write an introduction for the debate on: "{topic}"

Domain: {domain}
Number of rounds: {num_rounds}

Background context:
{research_summary[:500] if research_summary else 'General topic'}

Write a TV host introduction that:
1. Welcomes the audience
2. Introduces the topic with context
3. Poses 2-3 key questions
4. Explains the format briefly

Introduction:<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    try:
        # Use pro model for balanced/neutral content
        raw_intro = model_manager.generate_pro(
            prompt,
            max_tokens=400,
            temperature=0.7,
        )
        
        # Clean up the output
        intro_text = _clean_host_output(raw_intro)
        
        # Parse into components (simplified - use full text)
        return DebateIntroduction(
            opening="Welcome to tonight's debate!",
            topic_context=f"Topic: {topic}",
            key_questions=[],
            format_explanation=f"We'll have {num_rounds} rounds of debate.",
            full_introduction=intro_text,
        )
    except Exception as e:
        print(f"  ⚠ LLM introduction failed: {e}, using template")
        return _generate_template(topic, domain, research_summary, num_rounds)


def _clean_host_output(text: str) -> str:
    """Clean the host's generated introduction."""
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    
    # Remove meta-commentary
    remove_patterns = [
        r'Here is (?:the |my |a )?introduction.*?:',
        r'Introduction:',
        r'Note:.*?(?=\n|$)',
    ]
    for pattern in remove_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text
