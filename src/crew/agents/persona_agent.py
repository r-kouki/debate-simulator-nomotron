"""
Persona Recommendation Agent - Recommends real experts for debate panels.

Uses Wikipedia and internet search to find notable people who could
participate in a real-world version of the debate.
"""

from dataclasses import dataclass
from crewai import Agent

from src.crew.tools.internet_research import InternetResearchTool
from src.crew.tools.wikipedia_tool import WikipediaSearchTool


@dataclass
class DebateGuest:
    """Recommended debate panel guest."""
    name: str
    credentials: str
    known_stance: str  # "pro", "con", "neutral", or "unknown"
    bio: str
    source_url: str


def create_persona_agent(
    internet_tool: InternetResearchTool = None,
    wikipedia_tool: WikipediaSearchTool = None,
) -> Agent:
    """
    Create the persona recommendation agent.
    
    Args:
        internet_tool: Pre-configured InternetResearchTool
        wikipedia_tool: Pre-configured WikipediaSearchTool
        
    Returns:
        Persona recommendation Agent
    """
    tools = []
    
    if internet_tool is None:
        internet_tool = InternetResearchTool(use_internet=True)
    tools.append(internet_tool)
    
    if wikipedia_tool is None:
        wikipedia_tool = WikipediaSearchTool()
    tools.append(wikipedia_tool)
    
    return Agent(
        role="Debate Panel Curator",
        goal=(
            "Recommend 2-4 real-world experts who could participate in "
            "a TV debate on the given topic. Find people with relevant expertise "
            "and known positions on the subject."
        ),
        backstory=(
            "You are a TV producer specializing in debate shows. You have extensive "
            "knowledge of public intellectuals, academics, journalists, and advocates "
            "across many fields. You find guests who will create engaging, informed "
            "discussions - balancing different perspectives and expertise levels. "
            "You research each recommendation to provide their credentials and known stance."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def recommend_debate_guests(
    topic: str,
    domain: str,
    wikipedia_tool: WikipediaSearchTool,
    internet_tool: InternetResearchTool = None,
    num_guests: int = 4,
) -> list[DebateGuest]:
    """
    Recommend real-world debate guests for a topic.
    
    Args:
        topic: The debate topic
        domain: Domain category
        wikipedia_tool: Wikipedia search tool
        internet_tool: Optional internet search tool
        num_guests: Number of guests to recommend (default 4)
        
    Returns:
        List of DebateGuest recommendations
    """
    guests = []
    
    # Search Wikipedia for experts
    wiki_people = wikipedia_tool.search_experts_for_debate(topic)
    
    for person in wiki_people[:num_guests]:
        # Try to infer stance from bio
        stance = _infer_stance(person.bio, topic)
        
        guests.append(DebateGuest(
            name=person.name,
            credentials=_extract_credentials(person.bio),
            known_stance=stance,
            bio=person.bio,
            source_url=person.url,
        ))
    
    # Supplement with internet search if we need more guests
    if len(guests) < num_guests and internet_tool and internet_tool.use_internet:
        try:
            # Search for additional experts
            expert_results = internet_tool._run(topic, search_type="experts")
            # Parse results and add to guests (simplified)
            # In practice, you'd parse the formatted string or access raw results
        except Exception:
            pass  # Continue with Wikipedia results only
    
    return guests[:num_guests]


def _infer_stance(bio: str, topic: str) -> str:
    """
    Infer a person's likely stance on a topic from their bio.
    
    This is a simple heuristic - in practice, you'd want
    more sophisticated analysis.
    """
    bio_lower = bio.lower()
    topic_lower = topic.lower()
    
    # Pro indicators
    pro_words = ["advocate", "supporter", "proponent", "promotes", "champion"]
    # Con indicators  
    con_words = ["critic", "opponent", "skeptic", "against", "opposes"]
    
    pro_count = sum(1 for w in pro_words if w in bio_lower)
    con_count = sum(1 for w in con_words if w in bio_lower)
    
    if pro_count > con_count:
        return "pro"
    elif con_count > pro_count:
        return "con"
    else:
        return "unknown"


def _extract_credentials(bio: str) -> str:
    """Extract key credentials from a biography."""
    # Look for common credential patterns
    credential_patterns = [
        "professor", "doctor", "phd", "researcher", "scientist",
        "journalist", "author", "founder", "director", "ceo",
        "economist", "lawyer", "physician", "expert",
    ]
    
    bio_lower = bio.lower()
    found = [p for p in credential_patterns if p in bio_lower]
    
    if found:
        return ", ".join(found[:3]).title()
    else:
        return "Expert"
