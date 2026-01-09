"""
Debater Agents - Pro and Con debate argument generators.

Uses DebateGenerationTool with DualModelManager for
history-aware, adapter-enhanced argument generation.
"""

from crewai import Agent

from src.crew.tools.debate_tool import DebateGenerationTool


def create_pro_debater_agent(
    debate_tool: DebateGenerationTool,
) -> Agent:
    """
    Create the Pro debater agent.
    
    Args:
        debate_tool: Configured DebateGenerationTool with model manager
        
    Returns:
        Pro debater Agent
    """
    return Agent(
        role="Pro Debater",
        goal=(
            "Construct compelling arguments in FAVOR of the debate topic. "
            "Use evidence effectively and respond to counter-arguments. "
            "Keep responses concise: 5 sentences (max 8 if critical)."
        ),
        backstory=(
            "You are a skilled advocate who excels at building persuasive cases. "
            "You identify the strongest points in favor of a position and present them "
            "with clarity and conviction. You reference specific evidence, address "
            "counter-arguments thoughtfully, and maintain a respectful, professional tone. "
            "You understand that brevity is powerful - you make every sentence count."
        ),
        tools=[debate_tool],
        verbose=True,
        allow_delegation=False,
    )


def create_con_debater_agent(
    debate_tool: DebateGenerationTool,
) -> Agent:
    """
    Create the Con debater agent.
    
    Args:
        debate_tool: Configured DebateGenerationTool with model manager
        
    Returns:
        Con debater Agent
    """
    return Agent(
        role="Con Debater",
        goal=(
            "Construct compelling arguments AGAINST the debate topic. "
            "Identify weaknesses in pro arguments and present counter-evidence. "
            "Keep responses concise: 5 sentences (max 8 if critical)."
        ),
        backstory=(
            "You are a critical thinker who excels at identifying flaws in arguments. "
            "You find compelling counter-evidence and present alternative perspectives. "
            "You challenge assumptions, highlight risks, and question proposed solutions "
            "while maintaining intellectual honesty. You keep your arguments focused "
            "and impactful - every sentence serves a purpose."
        ),
        tools=[debate_tool],
        verbose=True,
        allow_delegation=False,
    )
