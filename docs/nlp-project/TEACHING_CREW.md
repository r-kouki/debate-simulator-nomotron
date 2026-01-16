# Teaching Crew Documentation

CrewAI-based educational content generation system for the Debate Simulator.

## Overview

The Teaching Crew is a separate module from the Debate Crew that focuses on **education** rather than argumentation. It generates structured lessons on any topic using:

1. **Wikipedia** for factual grounding
2. **Internet research** for current information
3. **Domain-specific LLM adapters** for specialized knowledge
4. **Structured parsing** for organized lesson output

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TeacherCrew                              │
│  src/crew/teacher_crew.py                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐  │
│  │Router Agent │ → │ Research Tools  │ → │  Teacher Agent   │  │
│  │(Domain)     │   │(Wiki + Internet)│   │(Lesson Gen)      │  │
│  └─────────────┘   └─────────────────┘   └──────────────────┘  │
│         │                   │                     │             │
│         ▼                   ▼                     ▼             │
│  ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐  │
│  │DualModel    │   │Session Cache    │   │Lesson Parser     │  │
│  │Manager      │   │                 │   │                  │  │
│  └─────────────┘   └─────────────────┘   └──────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Output        │
                    │ • lesson.md     │
                    │ • lesson.json   │
                    └─────────────────┘
```

## Components

### Core Files

| File | Description |
|------|-------------|
| `src/crew/teacher_crew.py` | Main orchestrator class |
| `src/crew/agents/teacher_agent.py` | Teacher agent + Lesson dataclass |
| `scripts/run_teacher.py` | CLI interface |

### Supporting Tools

| File | Description |
|------|-------------|
| `src/crew/tools/wikipedia_tool.py` | Wikipedia search integration |
| `src/crew/tools/internet_research.py` | DuckDuckGo web search |
| `src/crew/utils/dual_model_manager.py` | LLM + LoRA adapter management |
| `src/crew/agents/router_agent.py` | Topic domain classification |

### Frontend Components

| File | Description |
|------|-------------|
| `frontend-xp/src/components/LessonCreator/` | Lesson configuration UI |
| `frontend-xp/src/components/LessonViewer/` | Real-time lesson display with SSE |

## Quick Start

### CLI Usage

```bash
# Basic usage
python scripts/run_teacher.py "Quantum Computing"

# With detail level
python scripts/run_teacher.py "Climate Change" --level beginner
python scripts/run_teacher.py "Machine Learning" --level advanced

# Disable internet (Wikipedia + model knowledge only)
python scripts/run_teacher.py "History of Rome" --no-internet

# Custom output directory
python scripts/run_teacher.py "Photosynthesis" --output-dir my_lessons/

# Quiet mode
python scripts/run_teacher.py "Neural Networks" --quiet
```

### Python API

```python
from src.crew.teacher_crew import TeacherCrew

# Initialize
crew = TeacherCrew(
    use_internet=True,      # Enable web research
    output_dir="runs/lessons",
    verbose=True,
)

# Generate lesson
result = crew.teach(
    topic="Quantum Computing",
    detail_level="intermediate",  # beginner | intermediate | advanced
)

# Access results
print(result.topic)              # "Quantum Computing"
print(result.domain)             # "technology"
print(result.duration_seconds)   # ~50-60s

# Lesson content
lesson = result.lesson
print(lesson.overview)           # 2-3 paragraph introduction
print(lesson.key_concepts)       # List of 3-5 concepts
print(lesson.examples)           # List of 2-3 examples
print(lesson.quiz_questions)     # List of 2-3 review questions
print(lesson.further_reading)    # List of {title, url} dicts
```

## Pipeline Flow

The teaching pipeline executes in 4 steps:

```
Step 1: Domain Classification
    └─ Analyzes topic keywords
    └─ Returns: domain (education|medicine|ecology|technology|debate)
    └─ Confidence score for adapter selection

Step 2: Research Gathering
    ├─ Wikipedia summary (8 sentences)
    ├─ Wikipedia full article content
    └─ Internet search (if enabled)
    └─ Returns: concatenated research context

Step 3: Model & Adapter Loading
    └─ Loads Pro model instance
    └─ Applies domain-specific LoRA adapter
    └─ Defaults to "education" adapter

Step 4: Lesson Generation
    ├─ Builds structured prompt with research context
    ├─ Generates lesson text (max 800 tokens)
    └─ Parses into Lesson dataclass
    └─ Saves to disk (Markdown + JSON)
```

## Data Structures

### TeachingSession

Returned by `TeacherCrew.teach()`:

```python
@dataclass
class TeachingSession:
    topic: str              # Original topic
    domain: str             # Detected domain
    lesson: Lesson          # Structured lesson content
    research_context: str   # Raw research material
    duration_seconds: float # Generation time
    use_internet: bool      # Whether internet was used
```

### Lesson

Structured lesson content:

```python
@dataclass
class Lesson:
    topic: str                    # Lesson title
    overview: str                 # 2-3 paragraph introduction
    key_concepts: list[str]       # 3-5 key concepts with explanations
    examples: list[str]           # 2-3 concrete examples
    further_reading: list[dict]   # [{"title": "...", "url": "..."}]
    quiz_questions: list[str]     # 2-3 review questions
```

## Detail Levels

| Level | Description |
|-------|-------------|
| `beginner` | Simple language, basic concepts, no jargon |
| `intermediate` | Moderate detail, technical terms with explanations |
| `advanced` | Technical depth, nuanced analysis, advanced concepts |

## Domain Adapters

The router agent classifies topics into domains for adapter selection:

| Domain | Keywords |
|--------|----------|
| `education` | school, university, student, teacher, learning, curriculum |
| `medicine` | health, medical, doctor, hospital, treatment, disease |
| `ecology` | environment, climate, pollution, ecosystem, biodiversity |
| `technology` | AI, robot, software, computer, digital, internet |
| `debate` | (fallback for general topics) |

## Output Artifacts

Lessons are saved to `runs/lessons/{timestamp}_{topic_slug}/`:

```
runs/lessons/20250115_143022_Quantum_Computing/
├── lesson.md    # Formatted Markdown
└── lesson.json  # Structured JSON
```

### lesson.md Format

```markdown
# Quantum Computing

*Generated: 20250115_143022*
*Domain: technology*

## Overview

[2-3 paragraphs...]

## Key Concepts

- Concept 1: Explanation
- Concept 2: Explanation

## Examples

- Example 1
- Example 2

## Further Reading

- Resource title

## Review Questions

1. Question 1?
2. Question 2?
```

## Frontend Integration

### API Endpoints

The frontend expects these endpoints on port 5040:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/lessons` | Create a new lesson |
| `GET` | `/api/lessons/{id}` | Get lesson by ID |
| `GET` | `/api/lessons/{id}/stream` | SSE stream for real-time updates |

### Create Lesson Request

```json
POST /api/lessons
{
  "topic": "Quantum Computing",
  "detail_level": "intermediate",
  "use_internet": true
}
```

### SSE Events

The stream endpoint emits these events:

| Event | Description |
|-------|-------------|
| `lesson_started` | Lesson generation began |
| `lesson_progress` | Step update with progress percentage |
| `lesson_complete` | Lesson finished, includes full content |
| `error` | Generation failed |

```json
// lesson_progress
{
  "type": "lesson_progress",
  "step": "Researching",
  "message": "Gathering Wikipedia content",
  "progress": 25
}

// lesson_complete
{
  "type": "lesson_complete",
  "lesson": {
    "overview": "...",
    "key_concepts": [...],
    "examples": [...],
    "quiz_questions": [...],
    "further_reading": [...]
  }
}
```

## Configuration

### Enable/Disable Internet

```python
crew = TeacherCrew(use_internet=True)

# Or toggle at runtime
crew.disable_internet()
crew.enable_internet()
```

### Custom Output Directory

```python
from pathlib import Path
crew = TeacherCrew(output_dir=Path("my_lessons"))
```

## Dependencies

- **CrewAI 1.8.0**: Agent orchestration (installed with `--no-deps`)
- **Wikipedia**: Python library for Wikipedia content
- **DuckDuckGo**: Web search via `duckduckgo_search`
- **Hugging Face Transformers**: LLM inference
- **PEFT/LoRA**: Domain-specific adapters
- **PyTorch/CUDA**: GPU acceleration

## Comparison with Debate Crew

| Feature | TeacherCrew | DebateCrew |
|---------|-------------|------------|
| Purpose | Education | Argumentation |
| Model instances | 1 (Pro only) | 2 (Pro + Con) |
| Output | Structured lessons | Debate transcripts |
| Default adapter | education | domain-specific |
| Internet | Enabled by default | Disabled by default |

## Performance

- **Cold start**: ~30s (model loading)
- **Lesson generation**: ~20-30s
- **Total**: ~50-60s per lesson

## Example Output

```
╔══════════════════════════════════════════════════════════╗
║           CREWAI TEACHER                                 ║
║           Learn Any Topic                                ║
╚══════════════════════════════════════════════════════════╝

[1/4] Classifying topic domain...
  → Domain: technology (confidence: 0.85)
[2/4] Researching topic...
  → Gathered 4532 chars of context
[3/4] Loading domain knowledge...
[4/4] Generating lesson...

============================================================
LESSON GENERATED
============================================================
Duration: 52.3s

## Quantum Computing

### Overview
Quantum computing is a revolutionary approach to computation...

### Key Concepts
  • Qubit: The fundamental unit of quantum information...
  • Superposition: A qubit can exist in multiple states...
  • Entanglement: Quantum particles become correlated...

### Examples
  • Shor's algorithm for factoring large numbers
  • Grover's algorithm for database search

### Review Questions
  1. What makes a qubit different from a classical bit?
  2. How does quantum entanglement enable faster computation?
```
