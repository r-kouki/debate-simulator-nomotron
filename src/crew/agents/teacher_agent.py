"""
Teacher Agent - Provides educational content on topics.

Uses research tools to gather information and generates
structured lessons for users who want to learn about a subject.
"""

from dataclasses import dataclass
from crewai import Agent

from src.crew.tools.internet_research import InternetResearchTool
from src.crew.tools.wikipedia_tool import WikipediaSearchTool


@dataclass
class Lesson:
    """Structured educational lesson."""
    topic: str
    overview: str
    key_concepts: list[str]
    examples: list[str]
    further_reading: list[dict]  # [{title, url}]
    quiz_questions: list[str]


def create_teacher_agent(
    internet_tool: InternetResearchTool = None,
    wikipedia_tool: WikipediaSearchTool = None,
) -> Agent:
    """
    Create the teacher agent.
    
    Args:
        internet_tool: Pre-configured InternetResearchTool
        wikipedia_tool: Pre-configured WikipediaSearchTool
        
    Returns:
        Teacher Agent
    """
    tools = []
    
    if internet_tool is None:
        internet_tool = InternetResearchTool(use_internet=True)
    tools.append(internet_tool)
    
    if wikipedia_tool is None:
        wikipedia_tool = WikipediaSearchTool()
    tools.append(wikipedia_tool)
    
    return Agent(
        role="Educational Instructor",
        goal=(
            "Teach users about any topic they want to learn. "
            "Create clear, structured lessons with key concepts, "
            "examples, and further reading suggestions."
        ),
        backstory=(
            "You are an experienced educator with the ability to explain complex "
            "topics in accessible ways. You break down subjects into digestible parts, "
            "use relevant examples, and provide resources for deeper learning. "
            "You adapt your teaching style to the topic - technical subjects get "
            "precise explanations while philosophical topics explore multiple viewpoints."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def generate_lesson_prompt(
    topic: str,
    research_context: str,
    detail_level: str = "intermediate",
) -> str:
    """
    Generate a prompt for creating a structured lesson.
    
    Args:
        topic: The topic to teach
        research_context: Gathered research material
        detail_level: "beginner", "intermediate", or "advanced"
        
    Returns:
        Formatted prompt for lesson generation
    """
    level_instructions = {
        "beginner": "Use simple language and basic concepts. Avoid jargon.",
        "intermediate": "Include moderate detail and some technical terms with explanations.",
        "advanced": "Include technical depth, nuanced analysis, and advanced concepts.",
    }
    
    instruction = level_instructions.get(detail_level, level_instructions["intermediate"])
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert educator. Create a structured lesson on the given topic.

FORMAT YOUR RESPONSE AS:
## Overview
(2-3 paragraph introduction to the topic)

## Key Concepts
1. Concept name: Explanation
2. Concept name: Explanation
(3-5 key concepts)

## Examples
- Example 1: Description
- Example 2: Description
(2-3 concrete examples)

## Further Reading
1. Resource title - brief description
(2-3 suggestions)

## Quick Quiz
1. Question?
2. Question?
(2-3 review questions)

{instruction}<|eot_id|><|start_header_id|>user<|end_header_id|>

TOPIC: {topic}

RESEARCH CONTEXT:
{research_context[:2000]}

Create a comprehensive lesson on this topic.<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    return prompt


def parse_lesson_response(response: str, topic: str) -> Lesson:
    """
    Parse a generated lesson into structured format.
    
    Args:
        response: Raw generated lesson text
        topic: The lesson topic
        
    Returns:
        Structured Lesson object
    """
    import re
    
    # Extract sections using headers
    overview = ""
    key_concepts = []
    examples = []
    further_reading = []
    quiz_questions = []
    
    # Simple parsing (in practice, use more robust parsing)
    sections = re.split(r'##\s+', response)
    
    for section in sections:
        section_lower = section.lower()
        lines = section.strip().split('\n')
        
        if section_lower.startswith('overview'):
            overview = '\n'.join(lines[1:]).strip()
        
        elif section_lower.startswith('key concept'):
            for line in lines[1:]:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    key_concepts.append(line.lstrip('0123456789.-) '))
        
        elif section_lower.startswith('example'):
            for line in lines[1:]:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    examples.append(line.lstrip('0123456789.-) '))
        
        elif section_lower.startswith('further') or section_lower.startswith('reading'):
            for line in lines[1:]:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    further_reading.append({
                        "title": line.lstrip('0123456789.-) '),
                        "url": "",  # Would need actual URL extraction
                    })
        
        elif section_lower.startswith('quiz') or section_lower.startswith('question'):
            for line in lines[1:]:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    quiz_questions.append(line.lstrip('0123456789.-) '))
    
    return Lesson(
        topic=topic,
        overview=overview or "No overview generated.",
        key_concepts=key_concepts[:5],
        examples=examples[:3],
        further_reading=further_reading[:3],
        quiz_questions=quiz_questions[:3],
    )
