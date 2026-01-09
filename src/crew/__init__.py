"""
CrewAI-based debate orchestration system.

Provides multi-agent debate simulation with dual model instances,
internet research, Wikipedia integration, and dynamic adapter loading.
"""

from src.crew.debate_crew import DebateCrew
from src.crew.teacher_crew import TeacherCrew

__all__ = ["DebateCrew", "TeacherCrew"]
