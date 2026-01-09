"""CrewAI agent definitions for debate system."""

from src.crew.agents.router_agent import create_router_agent
from src.crew.agents.research_agent import create_research_agent
from src.crew.agents.debater_agents import create_pro_debater_agent, create_con_debater_agent
from src.crew.agents.factcheck_agent import create_factcheck_agent
from src.crew.agents.judge_agent import create_judge_agent
from src.crew.agents.persona_agent import create_persona_agent
from src.crew.agents.teacher_agent import create_teacher_agent

__all__ = [
    "create_router_agent",
    "create_research_agent",
    "create_pro_debater_agent",
    "create_con_debater_agent",
    "create_factcheck_agent",
    "create_judge_agent",
    "create_persona_agent",
    "create_teacher_agent",
]
