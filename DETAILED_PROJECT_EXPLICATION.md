# DETAILED PROJECT EXPLICATION - DEBATE SIMULATOR NOMOTRON

> **Complete Technical Documentation**
>
> This document provides an exhaustive explanation of the Multi-Agent Debate Simulator project, with special focus on the CrewAI orchestration system. This documentation is split across multiple files for comprehensive coverage.

---

## TABLE OF CONTENTS

### This File (Main Overview)
1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [Complete Project Structure](#3-complete-project-structure)
4. [Technology Stack](#4-technology-stack)
5. [System Requirements](#5-system-requirements)
6. [Quick Start Guide](#6-quick-start-guide)

### Additional Documentation Files
- **[DETAILED_PROJECT_EXPLICATION_CREWAI.md](./DETAILED_PROJECT_EXPLICATION_CREWAI.md)** - Complete CrewAI System Deep-Dive
- **[DETAILED_PROJECT_EXPLICATION_BACKEND.md](./DETAILED_PROJECT_EXPLICATION_BACKEND.md)** - Python Backend Architecture
- **[DETAILED_PROJECT_EXPLICATION_FRONTEND.md](./DETAILED_PROJECT_EXPLICATION_FRONTEND.md)** - Frontend & API Documentation
- **[DETAILED_PROJECT_EXPLICATION_EXAMPLES.md](./DETAILED_PROJECT_EXPLICATION_EXAMPLES.md)** - Data Flow & Complete Examples

---

## 1. EXECUTIVE SUMMARY

### 1.1 What Is This Project?

The **Debate Simulator Nomotron** is a sophisticated multi-agent AI system that orchestrates realistic debates between AI agents. The system uses:

- **Large Language Models (LLMs)**: Specifically Llama 3.1 Nemotron Nano 8B running locally on NVIDIA GPU
- **QLoRA Fine-Tuning**: Domain-specific adapters (education, medicine, ecology, technology) for specialized knowledge
- **CrewAI Framework**: Modern agent orchestration for complex multi-step workflows
- **Dual Model Architecture**: Two independent LLM instances for Pro and Con debaters
- **RAG (Retrieval-Augmented Generation)**: Wikipedia and internet research integration
- **Windows 98-Themed Frontend**: Nostalgic React UI with draggable windows

### 1.2 Key Innovations

| Innovation | Description |
|------------|-------------|
| **Dual Model System** | Two completely separate LLM instances allow true parallel thinking - Pro and Con don't share context or bias each other |
| **Dynamic Adapter Loading** | LoRA adapters swap at runtime without reloading the base model - switch from "education" to "medicine" domain in milliseconds |
| **Quality Refinement Loops** | Research automatically refines queries if quality score < 60%, ensuring debates are well-informed |
| **8-Step Pipeline** | Structured workflow: Topic Analysis → Research → Classification → Host Intro → Debate Rounds → Fact-Check → Judging → Guest Recommendations |
| **Aggressive Output Cleaning** | Removes all LLM artifacts (markdown, meta-commentary, instruction leakage) for natural speech |

### 1.3 Use Cases

1. **Academic Research**: Study AI argumentation, bias, and reasoning
2. **Educational Tool**: Generate balanced debates on any topic for learning
3. **Content Generation**: Create debate transcripts for media or entertainment
4. **Model Evaluation**: Compare base model vs fine-tuned adapter performance
5. **Prototype Development**: Test multi-agent architectures with real LLMs

---

## 2. PROJECT OVERVIEW

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   React Frontend    │  │   CLI Scripts       │  │   REST API Client   │ │
│  │  (Windows 98 Theme) │  │  (run_debate_crew)  │  │   (Any HTTP Client) │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
└─────────────┼─────────────────────────┼─────────────────────────┼───────────┘
              │                         │                         │
              ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server (Python)                           │   │
│  │    /health  /debates  /topics  /profiles  /debates/:id/stream       │   │
│  └──────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
│  ┌──────────────────────────────────┴──────────────────────────────────┐   │
│  │              Alternative: Fastify Server (Node.js)                   │   │
│  │                    Uses OpenRouter for LLM calls                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CREWAI ORCHESTRATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         DebateCrew                                   │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │   │Topic Analyst │→ │Research Agent│→ │Research      │              │   │
│  │   │              │  │              │  │Analyst       │              │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │          │                                    │                      │   │
│  │          ▼                                    ▼                      │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │   │TV Host Agent │→ │Pro Debater   │⇄ │Con Debater   │              │   │
│  │   │              │  │              │  │              │              │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                            │                  │                      │   │
│  │                            ▼                  ▼                      │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │   │Fact-Check    │→ │Judge Agent   │→ │Persona Agent │              │   │
│  │   │Agent         │  │              │  │(Optional)    │              │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MODEL LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DualModelManager                                  │   │
│  │   ┌────────────────────────┐  ┌────────────────────────┐            │   │
│  │   │     Model Instance 1   │  │    Model Instance 2    │            │   │
│  │   │   (Pro Debater LLM)    │  │   (Con Debater LLM)    │            │   │
│  │   │                        │  │                        │            │   │
│  │   │  Base: Llama 3.1       │  │  Base: Llama 3.1       │            │   │
│  │   │  Nemotron Nano 8B      │  │  Nemotron Nano 8B      │            │   │
│  │   │                        │  │                        │            │   │
│  │   │  Adapter: education/   │  │  Adapter: education/   │            │   │
│  │   │  medicine/ecology/etc  │  │  medicine/ecology/etc  │            │   │
│  │   └────────────────────────┘  └────────────────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    4-bit Quantization (QLoRA)                        │   │
│  │         ~6GB VRAM per model = ~12GB total for dual models           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RESEARCH LAYER                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │   Wikipedia Tool     │  │  Internet Research   │                        │
│  │                      │  │  Tool (DuckDuckGo)   │                        │
│  │  - Topic summaries   │  │                      │                        │
│  │  - Expert search     │  │  - Debate facts      │                        │
│  │  - Disambiguation    │  │  - Pro/Con evidence  │                        │
│  │  - Caching           │  │  - Quality scoring   │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   runs/debates/  │  │   data/splits/   │  │  models/adapters │          │
│  │                  │  │                  │  │                  │          │
│  │  - result.json   │  │  - train.jsonl   │  │  - education/    │          │
│  │  - transcript.txt│  │  - val.jsonl     │  │  - medicine/     │          │
│  │                  │  │  - test.jsonl    │  │  - ecology/      │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Two Backend Options

The project supports two backend implementations:

#### Option A: Python Backend (Recommended for Local LLM)

```
┌────────────────────────────────────────────────────────────────┐
│                   Python Backend Stack                          │
│                                                                 │
│  FastAPI Server → DebateCrew → DualModelManager → Local LLM    │
│                                                                 │
│  Pros:                                                          │
│  ✓ Full local processing (no API costs)                        │
│  ✓ QLoRA adapters for domain specialization                    │
│  ✓ Complete control over model behavior                         │
│  ✓ Academic evaluation ready                                    │
│                                                                 │
│  Cons:                                                          │
│  ✗ Requires NVIDIA GPU (10-12GB VRAM)                          │
│  ✗ ~1 minute initial model load time                           │
└────────────────────────────────────────────────────────────────┘
```

#### Option B: Node.js Backend (For Cloud LLM)

```
┌────────────────────────────────────────────────────────────────┐
│                   Node.js Backend Stack                         │
│                                                                 │
│  Fastify Server → OpenRouter API → Cloud LLM (Nemotron)        │
│                                                                 │
│  Pros:                                                          │
│  ✓ No GPU required                                             │
│  ✓ Instant startup                                             │
│  ✓ Simpler deployment                                          │
│                                                                 │
│  Cons:                                                          │
│  ✗ Requires OpenRouter API key                                 │
│  ✗ No custom adapters                                          │
│  ✗ API costs for usage                                         │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 The 8-Step Debate Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        DEBATE PIPELINE FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

Step 1: TOPIC ANALYSIS
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: Raw user topic ("should eletric cars be mandatory?")             │
│                                                                          │
│ Processing:                                                              │
│   • Grammar correction: "eletric" → "electric"                          │
│   • Key term extraction: ["electric", "cars", "mandatory"]              │
│   • Domain detection: "technology" (keyword matching)                    │
│   • Query generation: 6 optimized search queries                         │
│                                                                          │
│ Output: TopicAnalysis object                                            │
│   {                                                                      │
│     corrected_topic: "Should electric cars be mandatory?",              │
│     domain_hint: "technology",                                          │
│     research_queries: [                                                  │
│       "Should electric cars be mandatory debate 2026",                  │
│       "electric vehicles benefits advantages",                          │
│       "electric cars problems concerns",                                │
│       ...                                                                │
│     ]                                                                    │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: RESEARCH GATHERING
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: TopicAnalysis.research_queries                                   │
│                                                                          │
│ Processing:                                                              │
│   • Execute each query against Wikipedia API                            │
│   • Execute each query against DuckDuckGo (if use_internet=True)        │
│   • Apply quality scoring to results                                    │
│   • If score < 60: refine query and retry (max 5 attempts)              │
│   • Cache results per-session (MD5 hash keys)                           │
│                                                                          │
│ Output: Raw research context (concatenated text)                        │
│   "Electric vehicles (EVs) are automobiles that use one or more         │
│    electric motors for propulsion... According to IEA data, EV sales    │
│    increased by 35% in 2025... Critics argue that battery production    │
│    has significant environmental impact..."                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 3: RESEARCH CLASSIFICATION
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: Raw research context + topic                                     │
│                                                                          │
│ Processing:                                                              │
│   • Identify PRO indicators: "benefit", "advantage", "positive"         │
│   • Identify CON indicators: "problem", "risk", "negative", "concern"   │
│   • Extract statistics: numbers + units (%, million, billion)           │
│   • Extract key facts: "according to", "research shows"                 │
│   • Calculate quality score (0-100)                                     │
│                                                                          │
│ Output: ClassifiedResearch object                                       │
│   {                                                                      │
│     pro_points: [                                                        │
│       "EVs produce zero direct emissions",                              │
│       "Lower lifetime operating costs",                                 │
│       "35% sales growth indicates market demand"                        │
│     ],                                                                   │
│     con_points: [                                                        │
│       "Battery production has environmental impact",                    │
│       "Charging infrastructure gaps in rural areas",                    │
│       "Higher upfront purchase cost"                                    │
│     ],                                                                   │
│     statistics: ["35% growth", "80% lower fuel costs"],                 │
│     quality_score: 78                                                   │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 4: TV HOST INTRODUCTION
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: Topic + classified research                                      │
│                                                                          │
│ Processing:                                                              │
│   • Generate engaging opening (TV debate style)                         │
│   • List 3-5 key questions for the debate                               │
│   • Set the stage for both sides                                        │
│                                                                          │
│ Output: DebateIntroduction object                                       │
│   {                                                                      │
│     opening: "Good evening! Tonight we tackle a question that affects   │
│               every driver on the road: Should electric cars be         │
│               mandatory? With climate change accelerating and EV        │
│               technology advancing rapidly, this debate couldn't be     │
│               more timely...",                                           │
│     key_questions: [                                                     │
│       "Can the grid handle universal EV adoption?",                     │
│       "What about rural communities without charging infrastructure?",  │
│       "Is the environmental benefit real when considering batteries?"   │
│     ]                                                                    │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 5: DEBATE ROUNDS (repeated N times)
┌─────────────────────────────────────────────────────────────────────────┐
│ For each round (1 to num_rounds):                                       │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ PRO DEBATER (Model Instance 1)                                   │   │
│   │                                                                   │   │
│   │ Input:                                                            │   │
│   │   • Topic                                                         │   │
│   │   • Pro-specific research context                                 │   │
│   │   • Opponent's last argument (if round > 1)                       │   │
│   │   • Round number (affects opening vs rebuttal prompts)            │   │
│   │                                                                   │   │
│   │ Processing:                                                       │   │
│   │   • Load domain adapter (education, medicine, etc.)               │   │
│   │   • Generate argument using debate_tool._run()                    │   │
│   │   • Clean output (remove markdown, meta-commentary)               │   │
│   │   • Limit to 10 sentences max                                     │   │
│   │                                                                   │   │
│   │ Output: Pro argument string (5-10 sentences)                      │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ CON DEBATER (Model Instance 2)                                   │   │
│   │                                                                   │   │
│   │ Input:                                                            │   │
│   │   • Topic                                                         │   │
│   │   • Con-specific research context                                 │   │
│   │   • Pro's argument from this round (added to history)             │   │
│   │   • Round number                                                  │   │
│   │                                                                   │   │
│   │ Processing:                                                       │   │
│   │   • Same as Pro, but with Con-specific prompts                    │   │
│   │   • Explicitly addresses Pro's claims                             │   │
│   │                                                                   │   │
│   │ Output: Con argument string (5-10 sentences)                      │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│ History updated after each turn for next round's context                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 6: FACT-CHECKING
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: All pro_arguments[], all con_arguments[], research_context       │
│                                                                          │
│ Processing (for each side):                                             │
│   • Extract claims (sentences with 5+ words)                            │
│   • For each claim:                                                      │
│     - Tokenize into words, remove stopwords                             │
│     - Calculate word overlap with research (Jaccard-like)               │
│     - Score: overlap/max(len(claim_words), len(research_words))         │
│   • Aggregate scores:                                                    │
│     - avg_support_score = mean of all claim scores                      │
│     - faithfulness_score = supported_claims / total_claims              │
│                                                                          │
│ Output: Fact-check results                                              │
│   {                                                                      │
│     "pro": {                                                             │
│       "num_claims": 8,                                                   │
│       "supported_claims": 6,                                             │
│       "faithfulness_score": 0.75,                                        │
│       "verdict": "well_supported"                                        │
│     },                                                                   │
│     "con": {                                                             │
│       "num_claims": 7,                                                   │
│       "supported_claims": 4,                                             │
│       "faithfulness_score": 0.57,                                        │
│       "verdict": "partially_supported"                                   │
│     }                                                                    │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 7: JUDGING
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: pro_arguments[], con_arguments[], fact_check_results             │
│                                                                          │
│ Processing:                                                              │
│   For each argument, calculate 4 scores (0-25 each):                    │
│                                                                          │
│   LENGTH (0-25):                                                        │
│     • word_count = len(argument.split())                                │
│     • score = min(25, word_count * 25 / 100)                            │
│                                                                          │
│   LOGIC (0-25):                                                         │
│     • Count logical markers: "because", "therefore", "thus",            │
│       "consequently", "since", "as a result"                            │
│     • score = min(25, marker_count * 5)                                 │
│                                                                          │
│   EVIDENCE (0-25):                                                      │
│     • Count evidence markers: "study", "research", "data",              │
│       "percent", "%", "according to", "expert"                          │
│     • score = min(25, evidence_count * 5)                               │
│                                                                          │
│   CIVILITY (0-25):                                                      │
│     • Start with 25, subtract for aggressive language                   │
│     • Deductions: "stupid", "idiot", "nonsense", "ridiculous"           │
│     • score = max(0, 25 - deductions)                                   │
│                                                                          │
│   TOTAL = LENGTH + LOGIC + EVIDENCE + CIVILITY                          │
│   AVERAGE = sum(all argument totals) / num_arguments                    │
│                                                                          │
│   FINAL SCORE (with fact-check weight):                                 │
│     final = average * 0.7 + (faithfulness_score * 100) * 0.3            │
│                                                                          │
│   WINNER DETERMINATION:                                                 │
│     • If |pro_final - con_final| < 3: TIE                               │
│     • Else: higher score wins                                           │
│                                                                          │
│ Output: JudgeScore object                                               │
│   {                                                                      │
│     pro_score: 78,                                                       │
│     con_score: 72,                                                       │
│     winner: "pro",                                                       │
│     reasoning: "Pro wins with stronger evidence citations and           │
│                 higher fact-check faithfulness (0.75 vs 0.57).          │
│                 Con made compelling points but lacked specific data."   │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Step 8: GUEST RECOMMENDATIONS (Optional)
┌─────────────────────────────────────────────────────────────────────────┐
│ Input: Topic, domain, wikipedia_tool, internet_tool                     │
│                                                                          │
│ Processing:                                                              │
│   • Generate expert search queries:                                      │
│     - "[domain] expert [topic]"                                         │
│     - "[topic] professor researcher"                                    │
│     - "[topic] advocate critic"                                         │
│   • Search Wikipedia for notable people                                 │
│   • Cross-reference with web search                                     │
│   • Filter to ensure real people (not events/concepts)                  │
│   • Validate with bio indicators: "born", "is a", "professor"           │
│                                                                          │
│ Output: List of DebateGuest objects                                     │
│   [                                                                      │
│     {                                                                    │
│       name: "Mary Nichols",                                             │
│       title: "Former Chair, California Air Resources Board",            │
│       expertise: "EV policy and emissions regulation",                  │
│       relevance: "Key architect of California's EV mandate"             │
│     },                                                                   │
│     {                                                                    │
│       name: "Sandy Munro",                                              │
│       title: "Automotive Engineer and Analyst",                         │
│       expertise: "EV manufacturing and teardown analysis",              │
│       relevance: "Provides detailed cost/quality comparisons"           │
│     },                                                                   │
│     ...                                                                  │
│   ]                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. COMPLETE PROJECT STRUCTURE

```
debate-simulator-nomotron/
│
├── 📁 src/                                    # Python backend source code
│   │
│   ├── 📁 crew/                               # ★ CREWAI SYSTEM (Main Focus) ★
│   │   │
│   │   ├── 📄 debate_crew.py                  # Main orchestrator (568 lines)
│   │   │   └── DebateCrew class
│   │   │       ├── __init__()                 # Initialize with settings
│   │   │       ├── run_debate()               # Execute full 8-step pipeline
│   │   │       ├── _gather_research_with_queries()
│   │   │       ├── _generate_argument()       # Single argument generation
│   │   │       ├── _fact_check_debate()       # Verify claims
│   │   │       └── _save_artifacts()          # Persist results
│   │   │
│   │   ├── 📄 teacher_crew.py                 # Educational mode (120 lines)
│   │   │   └── TeacherCrew class
│   │   │       ├── teach()                    # Generate structured lesson
│   │   │       └── _generate_lesson()         # LLM-based content
│   │   │
│   │   ├── 📁 agents/                         # CrewAI Agent Definitions
│   │   │   ├── 📄 topic_analyst.py            # Grammar + query optimization
│   │   │   │   ├── TopicAnalysis dataclass
│   │   │   │   ├── GRAMMAR_CORRECTIONS dict
│   │   │   │   ├── DOMAIN_KEYWORDS dict
│   │   │   │   └── analyze_topic() function
│   │   │   │
│   │   │   ├── 📄 research_agent.py           # Wikipedia + Internet coordination
│   │   │   │   └── ResearchAgent class
│   │   │   │
│   │   │   ├── 📄 research_analyst.py         # PRO/CON classification
│   │   │   │   ├── ClassifiedResearch dataclass
│   │   │   │   └── analyze_research() function
│   │   │   │
│   │   │   ├── 📄 router_agent.py             # Domain classification
│   │   │   │   ├── DOMAIN_KEYWORDS dict
│   │   │   │   └── create_router_agent() function
│   │   │   │
│   │   │   ├── 📄 debater_agents.py           # Pro/Con argument generators
│   │   │   │   ├── create_pro_debater_agent()
│   │   │   │   └── create_con_debater_agent()
│   │   │   │
│   │   │   ├── 📄 factcheck_agent.py          # Claim verification
│   │   │   │   ├── STOPWORDS set
│   │   │   │   ├── compute_faithfulness_score()
│   │   │   │   └── create_factcheck_agent()
│   │   │   │
│   │   │   ├── 📄 judge_agent.py              # Scoring + winner determination
│   │   │   │   ├── JudgeScore dataclass
│   │   │   │   ├── judge_debate() function
│   │   │   │   └── _score_argument() helper
│   │   │   │
│   │   │   ├── 📄 persona_agent.py            # Expert recommendations
│   │   │   │   ├── DebateGuest dataclass
│   │   │   │   ├── recommend_debate_guests()
│   │   │   │   └── _is_real_person() validator
│   │   │   │
│   │   │   ├── 📄 tv_host_agent.py            # Debate introduction
│   │   │   │   ├── DebateIntroduction dataclass
│   │   │   │   └── generate_tv_host_introduction()
│   │   │   │
│   │   │   └── 📄 teacher_agent.py            # Lesson generation
│   │   │       ├── Lesson dataclass
│   │   │       └── create_teacher_agent()
│   │   │
│   │   ├── 📁 tools/                          # CrewAI Tool Implementations
│   │   │   ├── 📄 debate_tool.py              # Argument generation (432 lines)
│   │   │   │   ├── DebateTurn dataclass
│   │   │   │   ├── DebateGenerationTool class
│   │   │   │   │   ├── _run()                 # Main generation method
│   │   │   │   │   ├── _build_prompt()        # Opening vs rebuttal
│   │   │   │   │   ├── _clean_output()        # Remove LLM artifacts
│   │   │   │   │   └── add_external_turn()    # History management
│   │   │   │   └── OPENING_PROMPT, REBUTTAL_PROMPT templates
│   │   │   │
│   │   │   ├── 📄 internet_research.py        # Web search with caching
│   │   │   │   ├── InternetResearchTool class
│   │   │   │   │   ├── _run()                 # Execute search
│   │   │   │   │   ├── _search_debate()       # Debate-focused search
│   │   │   │   │   └── _search_debate_with_refinement()
│   │   │   │   └── Session caching (MD5 keys)
│   │   │   │
│   │   │   ├── 📄 wikipedia_tool.py           # Wikipedia access
│   │   │   │   ├── WikipediaSearchTool class
│   │   │   │   │   ├── _run()                 # Execute query
│   │   │   │   │   └── search_type: summary/experts/full
│   │   │   │   └── Disambiguation handling
│   │   │   │
│   │   │   └── 📄 research_evaluator.py       # Quality scoring
│   │   │       ├── ResearchEvaluation dataclass
│   │   │       ├── evaluate_research_quality()
│   │   │       ├── ISSUE_CATEGORIES dict
│   │   │       └── Scoring rubric (0-100)
│   │   │
│   │   └── 📁 utils/
│   │       └── 📄 dual_model_manager.py       # Two LLM instances (277 lines)
│   │           ├── DualModelManager class
│   │           │   ├── model_pro property     # Lazy-loaded Pro model
│   │           │   ├── model_con property     # Lazy-loaded Con model
│   │           │   ├── load_adapter()         # Dynamic adapter loading
│   │           │   ├── generate_pro()         # Pro generation
│   │           │   ├── generate_con()         # Con generation
│   │           │   └── get_memory_stats()     # VRAM usage
│   │           └── Adapter path management
│   │
│   ├── 📁 agents/                             # Original multi-agent system (legacy)
│   │   ├── 📄 base.py                         # Agent ABC + state machine
│   │   │   ├── AgentState enum
│   │   │   ├── DebateTurn dataclass
│   │   │   ├── JudgeScore dataclass
│   │   │   ├── DebateContext dataclass
│   │   │   └── Agent abstract class
│   │   │
│   │   ├── 📄 router.py                       # DomainRouterAgent
│   │   ├── 📄 research.py                     # ResearchAgent (BM25)
│   │   ├── 📄 debater.py                      # DebaterAgent
│   │   ├── 📄 factcheck.py                    # FactCheckAgent
│   │   ├── 📄 judge.py                        # JudgeAgent
│   │   └── 📄 logger.py                       # LoggerAgent
│   │
│   ├── 📁 orchestration/
│   │   └── 📄 pipeline.py                     # DebatePipeline state machine
│   │       ├── DebatePipeline class
│   │       │   ├── run()                      # Main execution loop
│   │       │   ├── _transition()              # State transitions
│   │       │   └── _process_state()           # Per-state logic
│   │       └── State flow: ROUTING → ... → COMPLETE
│   │
│   ├── 📁 serving/                            # FastAPI server
│   │   ├── 📄 api.py                          # REST endpoints
│   │   │   ├── /health
│   │   │   ├── /topics/search
│   │   │   ├── /topics/{topic_id}
│   │   │   ├── /debates (POST)
│   │   │   ├── /debates/{id}/next-turn (POST)
│   │   │   ├── /debates/{id}/turns (POST)
│   │   │   ├── /debates/{id}/turns/stream (POST) - SSE
│   │   │   └── /debates/{id}/score (POST)
│   │   │
│   │   ├── 📄 models.py                       # Pydantic schemas
│   │   │   ├── StartDebateRequest
│   │   │   ├── StartDebateResponse
│   │   │   ├── SendTurnRequest
│   │   │   ├── SendTurnResponse
│   │   │   └── ScoreDebateResponse
│   │   │
│   │   ├── 📄 debate_service.py               # Session management
│   │   │   ├── DebateSession dataclass
│   │   │   └── DebateService class
│   │   │
│   │   ├── 📄 profile.py                      # User profile storage
│   │   │   └── JSON-based persistence
│   │   │
│   │   └── 📄 topics.py                       # Topic database
│   │       └── TopicSearchService class
│   │
│   ├── 📁 train/                              # Training pipeline
│   │   ├── 📄 dataset.py                      # JSONL loading
│   │   │   ├── load_dataset()
│   │   │   └── tokenize_dataset()
│   │   │
│   │   └── 📄 trainer.py                      # QLoRA training
│   │       ├── TrainingMetrics dataclass
│   │       ├── MetricsCallback class
│   │       └── get_training_arguments()
│   │
│   └── 📁 utils/
│       ├── 📄 model_loader.py                 # Model loading utilities
│       │   ├── get_bnb_config()               # 4-bit quantization
│       │   ├── get_lora_config()              # LoRA hyperparameters
│       │   ├── load_base_model()              # Load Llama 3.1 Nemotron
│       │   ├── load_model_with_adapter()      # Load with LoRA
│       │   └── prepare_model_for_training()   # Add LoRA layers
│       │
│       └── 📄 web_search.py                   # DuckDuckGo wrapper
│
├── 📁 frontend/                               # React + TypeScript + Vite
│   ├── 📁 src/
│   │   ├── 📁 api/                            # API layer
│   │   │   ├── 📁 adapters/
│   │   │   │   ├── mock.ts                    # Mock API for testing
│   │   │   │   └── openRouter.ts              # OpenRouter integration
│   │   │   ├── 📁 hooks/                      # React Query hooks
│   │   │   │   ├── useHealth.ts
│   │   │   │   ├── useStartDebate.ts
│   │   │   │   ├── useNextTurn.ts
│   │   │   │   ├── useSendTurn.ts
│   │   │   │   ├── useScoreDebate.ts
│   │   │   │   ├── useTopics.ts
│   │   │   │   └── useProfile.ts
│   │   │   └── client.ts                      # Base API client
│   │   │
│   │   ├── 📁 components/                     # UI Components
│   │   │   ├── WindowFrame.tsx                # Draggable windows
│   │   │   ├── Taskbar.tsx                    # Bottom bar
│   │   │   ├── StartMenu.tsx                  # Windows menu
│   │   │   ├── Desktop.tsx                    # Main canvas
│   │   │   ├── ContextMenu.tsx                # Right-click menus
│   │   │   ├── DialogHost.tsx                 # Modal dialogs
│   │   │   ├── Tabs.tsx                       # Tab navigation
│   │   │   └── ToastContainer.tsx             # Notifications
│   │   │
│   │   ├── 📁 features/                       # Feature modules
│   │   │   ├── 📁 debate/                     # Debate UI
│   │   │   ├── 📁 topics/                     # Topic browser
│   │   │   ├── 📁 profile/                    # User profile
│   │   │   └── 📁 settings/                   # Settings panel
│   │   │
│   │   └── 📁 state/                          # Zustand stores
│   │       ├── windowStore.ts                 # Window management
│   │       ├── debateStore.ts                 # Debate state
│   │       ├── settingsStore.ts               # User preferences
│   │       └── profileStore.ts                # Player profile
│   │
│   ├── 📁 apps/api/                           # Optional Node.js backend
│   │   ├── 📁 src/
│   │   │   ├── 📁 routes/                     # Fastify routes
│   │   │   │   ├── health.ts
│   │   │   │   ├── profile.ts
│   │   │   │   ├── topics.ts
│   │   │   │   └── debates.ts
│   │   │   └── 📁 agents/                     # Simplified agents
│   │   │       ├── researchAgent.ts
│   │   │       ├── debaterAgent.ts
│   │   │       └── judgeAgent.ts
│   │   └── 📁 prisma/                         # Database schema
│   │       └── schema.prisma                  # SQLite schema
│   │
│   └── 📁 packages/contracts/                 # Shared schemas
│       └── 📁 src/
│           └── index.ts                       # Zod schemas
│
├── 📁 scripts/                                # Executable Python scripts
│   ├── 📄 run_debate_crew.py                  # ★ Main CLI entry point ★
│   ├── 📄 run_debate.py                       # Legacy debate script
│   ├── 📄 run_server.py                       # FastAPI server
│   ├── 📄 run_teacher.py                      # Teacher crew CLI
│   ├── 📄 verify_base_model.py                # Model loading test
│   ├── 📄 generate_education_dataset.py       # Dataset generation
│   ├── 📄 train_education_adapter.py          # QLoRA training
│   ├── 📄 evaluate_education_adapter.py       # Adapter evaluation
│   └── 📄 generate_academic_report.py         # Report generation
│
├── 📁 models/                                 # Model storage
│   ├── 📁 base/
│   │   └── 📁 llama3.1-nemotron-nano-8b-v1/   # Base LLM (~8GB)
│   │       ├── config.json
│   │       ├── model.safetensors
│   │       ├── tokenizer.json
│   │       └── ...
│   │
│   └── 📁 adapters/                           # LoRA adapters (~2-4MB each)
│       ├── 📁 education/
│       │   ├── adapter_config.json
│       │   └── adapter_model.safetensors
│       ├── 📁 medicine/
│       ├── 📁 ecology/
│       ├── 📁 technology/
│       └── 📁 debate/
│
├── 📁 data/
│   ├── 📁 splits/                             # Training datasets
│   │   ├── 📁 education/
│   │   │   ├── train.jsonl
│   │   │   ├── val.jsonl
│   │   │   └── test.jsonl
│   │   ├── 📁 medicine/
│   │   └── ...
│   ├── 📁 profiles/                           # User profiles
│   └── 📁 cache/                              # HuggingFace cache
│
├── 📁 runs/                                   # Output artifacts
│   ├── 📁 train/                              # Training checkpoints
│   ├── 📁 eval/                               # Evaluation results
│   ├── 📁 debates/                            # Debate transcripts
│   │   └── 📁 {timestamp}_{topic}/
│   │       ├── result.json
│   │       └── transcript.txt
│   └── 📁 reports/                            # Academic reports
│
├── 📁 configs/                                # Configuration files
│   └── training_config.yaml
│
├── 📁 test_outputs/                           # Test results
│   └── STANDALONE_TEST_SUMMARY.md
│
├── 📄 requirements.txt                        # Python dependencies
├── 📄 CLAUDE.md                               # Project instructions
├── 📄 ARCHITECTURE.md                         # System design
├── 📄 Dockerfile.backend                      # Backend container
├── 📄 Dockerfile.frontend                     # Frontend container
├── 📄 docker-compose.yml                      # Multi-container setup
└── 📄 nginx.conf                              # Reverse proxy config
```

---

## 4. TECHNOLOGY STACK

### 4.1 Python Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **LLM Framework** | Transformers | 4.x | Model loading and inference |
| **Quantization** | BitsAndBytes | 0.x | 4-bit quantization (QLoRA) |
| **Fine-tuning** | PEFT | 0.x | LoRA adapter training |
| **Agent Framework** | CrewAI | 1.8.0 | Multi-agent orchestration |
| **Web Framework** | FastAPI | 0.x | REST API server |
| **Async Runtime** | Uvicorn | 0.x | ASGI server |
| **Validation** | Pydantic | 2.x | Request/response schemas |
| **ML Compute** | PyTorch | 2.x | Tensor operations |
| **CUDA** | NVIDIA CUDA | 12.x | GPU acceleration |

### 4.2 Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | React | 18.x | UI components |
| **Language** | TypeScript | 5.x | Type safety |
| **Build Tool** | Vite | 5.x | Fast development |
| **State Management** | Zustand | 4.x | Global state |
| **Data Fetching** | React Query | 5.x | API caching |
| **Styling** | CSS Modules | - | Scoped styles |
| **Testing** | Vitest | 1.x | Unit tests |
| **Linting** | ESLint | 8.x | Code quality |

### 4.3 Node.js Backend (Alternative)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | Fastify | 4.x | High-performance HTTP |
| **Database** | Prisma + SQLite | 5.x | Data persistence |
| **LLM API** | OpenRouter | - | Cloud LLM access |
| **Validation** | Zod | 3.x | Schema validation |

### 4.4 DevOps

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containers** | Docker | Reproducible builds |
| **Orchestration** | Docker Compose | Multi-service setup |
| **Reverse Proxy** | Nginx | Load balancing |

---

## 5. SYSTEM REQUIREMENTS

### 5.1 Hardware Requirements

#### Minimum (Inference Only)
- **GPU**: NVIDIA with 8GB VRAM (RTX 3070, RTX 4060)
- **RAM**: 16GB system memory
- **Storage**: 20GB free space
- **CPU**: Any modern 4-core processor

#### Recommended (Full Dual Model)
- **GPU**: NVIDIA with 12GB+ VRAM (RTX 3090, RTX 4080, RTX 4090)
- **RAM**: 32GB system memory
- **Storage**: 50GB free space (models + datasets + outputs)
- **CPU**: 8-core processor recommended

#### Training Requirements
- **GPU**: NVIDIA with 16GB+ VRAM
- **RAM**: 64GB system memory recommended
- **Storage**: 100GB+ for checkpoints

### 5.2 Software Requirements

```bash
# Operating System
- Linux (Ubuntu 22.04+ recommended)
- Windows 11 with WSL2
- macOS (CPU-only, no training)

# Python
- Python 3.12+
- pip or conda

# CUDA
- CUDA Toolkit 12.x
- cuDNN 8.x

# Node.js (for frontend)
- Node.js 18+
- npm 9+

# Git
- Git 2.x
```

### 5.3 VRAM Usage Breakdown

| Configuration | VRAM Usage | Notes |
|---------------|------------|-------|
| Single model (inference) | ~6 GB | 4-bit quantized |
| Dual models (inference) | ~12 GB | Pro + Con instances |
| Single model + training | ~10 GB | Gradient checkpointing |
| Full training | ~16 GB | No gradient checkpointing |

---

## 6. QUICK START GUIDE

### 6.1 Installation

```bash
# Clone repository
git clone <repository-url>
cd debate-simulator-nomotron

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify GPU access
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Verify base model loads
python scripts/verify_base_model.py
```

### 6.2 Running a Debate (CLI)

```bash
# Simple debate (2 rounds, no internet)
python scripts/run_debate_crew.py "Should college be free?"

# Full-featured debate
python scripts/run_debate_crew.py \
  "Should artificial intelligence be regulated?" \
  --rounds 3 \
  --use-internet \
  --recommend-guests

# Quiet mode (less output)
python scripts/run_debate_crew.py "Your topic" --quiet
```

### 6.3 Running the Web Application

```bash
# Terminal 1: Start Python API server
python scripts/run_server.py

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev

# Open browser: http://localhost:5173
```

### 6.4 Training a Custom Adapter

```bash
# Generate training dataset
python scripts/generate_education_dataset.py

# Train adapter (adjust epochs/batch size for your VRAM)
python scripts/train_education_adapter.py

# Evaluate adapter vs base model
python scripts/evaluate_education_adapter.py

# Generate report with visualizations
python scripts/generate_academic_report.py
```

---

## NEXT: CrewAI Deep-Dive

Continue to **[DETAILED_PROJECT_EXPLICATION_CREWAI.md](./DETAILED_PROJECT_EXPLICATION_CREWAI.md)** for complete documentation of:

- DebateCrew class internals
- DualModelManager implementation
- All 11 CrewAI agents in detail
- All 4 CrewAI tools in detail
- Prompt engineering techniques
- Output cleaning algorithms
- Quality refinement loops

---

*Generated: 2026-01-11*
*Project: Debate Simulator Nomotron*
