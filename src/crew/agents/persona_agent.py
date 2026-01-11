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
    
    Uses a multi-pronged search strategy:
    1. Search for specific expert types (economists, professors, analysts)
    2. Search for people associated with the topic
    3. Cross-reference with web search for recent commentary
    4. Filter to ensure only real people are returned
    
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
    seen_names = set()
    
    # Extract key topic words for more targeted search
    topic_words = [w for w in topic.lower().split() if len(w) > 3]
    main_subject = " ".join(topic_words[:2]) if topic_words else topic
    
    # Domain-specific expert types
    expert_types = {
        "economics": ["economist", "professor of economics", "financial analyst"],
        "medicine": ["doctor", "medical researcher", "professor of medicine"],
        "education": ["education researcher", "professor of education", "teacher"],
        "ecology": ["environmental scientist", "climate researcher", "ecologist"],
        "politics": ["political scientist", "policy analyst", "politician"],
        "technology": ["tech researcher", "computer scientist", "AI researcher"],
        "debate": ["analyst", "professor", "researcher", "commentator"],
    }
    
    expert_roles = expert_types.get(domain.lower(), expert_types["debate"])
    
    # Strategy 1: Search for specific expert types related to topic
    for role in expert_roles[:2]:
        search_query = f"{main_subject} {role}"
        try:
            wiki_people = wikipedia_tool.search_experts_for_debate(search_query)
            for person in wiki_people:
                if person.name not in seen_names and _is_real_person(person.bio):
                    seen_names.add(person.name)
                    guests.append(DebateGuest(
                        name=person.name,
                        credentials=_extract_credentials(person.bio),
                        known_stance=_infer_stance(person.bio, topic),
                        bio=person.bio,
                        source_url=person.url,
                    ))
                    if len(guests) >= num_guests:
                        return guests
        except Exception as e:
            print(f"  ⚠ Expert search failed for {role}: {e}")
    
    # Strategy 2: Search for people directly named in topic context
    name_queries = [
        f"who is expert on {topic}",
        f"{topic} notable figure scholar",
        f"famous {main_subject} researcher professor",
    ]
    
    for query in name_queries:
        if len(guests) >= num_guests:
            break
        try:
            wiki_people = wikipedia_tool.search_experts_for_debate(query)
            for person in wiki_people:
                if person.name not in seen_names and _is_real_person(person.bio):
                    seen_names.add(person.name)
                    guests.append(DebateGuest(
                        name=person.name,
                        credentials=_extract_credentials(person.bio),
                        known_stance=_infer_stance(person.bio, topic),
                        bio=person.bio,
                        source_url=person.url,
                    ))
                    if len(guests) >= num_guests:
                        break
        except Exception:
            continue
    
    # Strategy 3: Supplement with internet search for recent experts
    if len(guests) < num_guests and internet_tool and internet_tool.use_internet:
        try:
            expert_results = internet_tool._run(topic, search_type="experts")
            # Parse looking for names (simple heuristic: capitalized words)
            import re
            potential_names = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+)', expert_results)
            for name in potential_names[:3]:
                if name not in seen_names and len(name) > 5:
                    try:
                        wiki_check = wikipedia_tool._run(name, search_type="summary", sentences=2)
                        if "born" in wiki_check.lower() or "is a" in wiki_check.lower():
                            seen_names.add(name)
                            guests.append(DebateGuest(
                                name=name,
                                credentials=_extract_credentials(wiki_check),
                                known_stance="unknown",
                                bio=wiki_check[:200],
                                source_url=f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}",
                            ))
                            if len(guests) >= num_guests:
                                break
                    except Exception:
                        continue
        except Exception:
            pass
    
    return guests[:num_guests]


def _is_real_person(bio: str) -> bool:
    """
    Check if a bio describes a real person (not an event, concept, or organization).
    
    Looks for birth indicators, occupations, and personal pronouns.
    """
    if not bio or len(bio) < 50:
        return False
    
    bio_lower = bio.lower()
    
    # Strong indicators it's a person
    person_indicators = [
        "born", "was born", "is a ", "is an ",
        "professor", "economist", "scientist", "researcher",
        "journalist", "author", "politician", "activist",
        "he was", "she was", "he is", "she is",
        "his career", "her career", "graduated",
    ]
    
    # Strong indicators it's NOT a person (it's an event, concept, or article)
    not_person_indicators = [
        "is the name of", "refers to", "was an event",
        "is a policy", "is a term", "was a period",
        "presidency of", "administration of", "government of",
        "is a company", "is an organization",
    ]
    
    # Check for disqualifying patterns first
    for indicator in not_person_indicators:
        if indicator in bio_lower:
            return False
    
    # Check for person indicators
    person_score = sum(1 for ind in person_indicators if ind in bio_lower)
    return person_score >= 2


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
