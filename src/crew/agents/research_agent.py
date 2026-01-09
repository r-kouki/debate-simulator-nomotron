"""
Research Agent - Gathers evidence and context for debates.

Uses InternetResearchTool and WikipediaSearchTool to find
relevant information for debate topics.
"""

from crewai import Agent

from src.crew.tools.internet_research import InternetResearchTool
from src.crew.tools.wikipedia_tool import WikipediaSearchTool


def create_research_agent(
    use_internet: bool = True,
    internet_tool: InternetResearchTool = None,
    wikipedia_tool: WikipediaSearchTool = None,
) -> Agent:
    """
    Create the research agent.
    
    Args:
        use_internet: Whether to enable internet research
        internet_tool: Pre-configured InternetResearchTool (optional)
        wikipedia_tool: Pre-configured WikipediaSearchTool (optional)
        
    Returns:
        Configured research Agent
    """
    # Initialize tools if not provided
    if internet_tool is None:
        internet_tool = InternetResearchTool(use_internet=use_internet)
    else:
        internet_tool.use_internet = use_internet
    
    if wikipedia_tool is None:
        wikipedia_tool = WikipediaSearchTool()
    
    tools = [internet_tool, wikipedia_tool]
    
    return Agent(
        role="Research Assistant",
        goal=(
            "Gather comprehensive, balanced evidence and context for debate topics. "
            "Find credible sources for both pro and con positions."
        ),
        backstory=(
            "You are an academic researcher with expertise in information synthesis. "
            "You search multiple sources - web articles, Wikipedia, and academic references - "
            "to compile balanced, well-sourced evidence. You present facts objectively "
            "without bias toward either side of a debate."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )
