# CREWAI SYSTEM DEEP-DIVE

> **Complete Technical Documentation of the CrewAI Orchestration System**
>
> This document provides exhaustive coverage of every component in the CrewAI-based debate system.

---

## TABLE OF CONTENTS

1. [CrewAI Integration Overview](#1-crewai-integration-overview)
2. [DebateCrew Class - The Main Orchestrator](#2-debatecrew-class---the-main-orchestrator)
3. [DualModelManager - Two LLM Instances](#3-dualmodelmanager---two-llm-instances)
4. [All 11 CrewAI Agents](#4-all-11-crewai-agents)
5. [All 4 CrewAI Tools](#5-all-4-crewai-tools)
6. [Prompt Engineering Techniques](#6-prompt-engineering-techniques)
7. [Output Cleaning Algorithms](#7-output-cleaning-algorithms)
8. [Quality Refinement System](#8-quality-refinement-system)
9. [Caching Strategy](#9-caching-strategy)
10. [Error Handling](#10-error-handling)

---

## 1. CREWAI INTEGRATION OVERVIEW

### 1.1 What is CrewAI?

CrewAI is a Python framework for orchestrating autonomous AI agents. In this project, it provides:

- **Agent Definitions**: Role-based AI personas with specific goals and backstories
- **Task Management**: Structured work units that agents complete
- **Tool Integration**: External capabilities (search, generation, etc.) that agents can use
- **Workflow Orchestration**: Sequential and parallel task execution

### 1.2 Why CrewAI for This Project?

| Feature | Benefit |
|---------|---------|
| **Role-based Agents** | Natural mapping to debate roles (Pro, Con, Judge, etc.) |
| **Tool Abstraction** | Clean separation between agent logic and external systems |
| **Flexible Workflows** | Support for both sequential and parallel execution |
| **Built-in Logging** | Easy debugging and monitoring |

### 1.3 CrewAI Installation Note

CrewAI 1.8.0 was installed with `--no-deps` to avoid conflicts with vLLM:

```bash
pip install --no-deps crewai==1.8.0 crewai-tools==1.8.0
```

This works because existing packages (openai 2.14.0, pydantic 2.12.5, tokenizers 0.22.1) satisfy CrewAI's requirements.

### 1.4 File Structure

```
src/crew/
├── debate_crew.py              # Main orchestrator (568 lines)
├── teacher_crew.py             # Educational mode (120 lines)
│
├── agents/                     # Agent definitions
│   ├── topic_analyst.py        # Grammar + query optimization
│   ├── research_agent.py       # Research coordination
│   ├── research_analyst.py     # PRO/CON classification
│   ├── router_agent.py         # Domain classification
│   ├── debater_agents.py       # Pro/Con generators
│   ├── factcheck_agent.py      # Claim verification
│   ├── judge_agent.py          # Scoring + winner
│   ├── persona_agent.py        # Expert recommendations
│   ├── tv_host_agent.py        # Debate introduction
│   └── teacher_agent.py        # Lesson generation
│
├── tools/                      # Tool implementations
│   ├── debate_tool.py          # Argument generation (432 lines)
│   ├── internet_research.py    # Web search
│   ├── wikipedia_tool.py       # Wikipedia access
│   └── research_evaluator.py   # Quality scoring
│
└── utils/
    └── dual_model_manager.py   # Two LLM instances (277 lines)
```

---

## 2. DEBATECREW CLASS - THE MAIN ORCHESTRATOR

**File**: `src/crew/debate_crew.py` (568 lines)

### 2.1 Class Definition

```python
class DebateCrew:
    """CrewAI-based debate orchestration with dual model instances."""

    def __init__(
        self,
        use_internet: bool = False,
        output_dir: Path = Path("runs/debates"),
        verbose: bool = True,
    ):
        """
        Initialize DebateCrew.

        Args:
            use_internet: Enable web search (slower but more informed)
            output_dir: Directory for saving debate artifacts
            verbose: Print progress messages
        """
        self.use_internet = use_internet
        self.output_dir = output_dir
        self.verbose = verbose

        # Lazy-loaded components
        self._model_manager: DualModelManager | None = None
        self._wikipedia_tool: WikipediaSearchTool | None = None
        self._internet_tool: InternetResearchTool | None = None
        self._pro_debate_tool: DebateGenerationTool | None = None
        self._con_debate_tool: DebateGenerationTool | None = None
```

### 2.2 Lazy Loading Pattern

All heavy resources are lazy-loaded on first access to minimize startup time:

```python
@property
def model_manager(self) -> DualModelManager:
    """Lazy-load dual model manager."""
    if self._model_manager is None:
        if self.verbose:
            print("Loading dual model manager...")
        self._model_manager = DualModelManager()
    return self._model_manager

@property
def wikipedia_tool(self) -> WikipediaSearchTool:
    """Lazy-load Wikipedia tool."""
    if self._wikipedia_tool is None:
        self._wikipedia_tool = WikipediaSearchTool()
    return self._wikipedia_tool

@property
def internet_tool(self) -> InternetResearchTool:
    """Lazy-load internet research tool."""
    if self._internet_tool is None:
        self._internet_tool = InternetResearchTool()
    return self._internet_tool

@property
def pro_debate_tool(self) -> DebateGenerationTool:
    """Lazy-load Pro debater tool."""
    if self._pro_debate_tool is None:
        self._pro_debate_tool = DebateGenerationTool(
            model_manager=self.model_manager,
            stance="pro",
        )
    return self._pro_debate_tool

@property
def con_debate_tool(self) -> DebateGenerationTool:
    """Lazy-load Con debater tool."""
    if self._con_debate_tool is None:
        self._con_debate_tool = DebateGenerationTool(
            model_manager=self.model_manager,
            stance="con",
        )
    return self._con_debate_tool
```

### 2.3 Main Method: run_debate()

```python
def run_debate(
    self,
    topic: str,
    num_rounds: int = 2,
    recommend_guests: bool = False,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> DebateResult:
    """
    Run a complete debate on the given topic.

    Args:
        topic: The debate topic/question
        num_rounds: Number of debate rounds (1-5 recommended)
        recommend_guests: Search for real experts to recommend
        progress_callback: Optional callback for UI updates
            - Called with (stage_name: str, progress: float)
            - progress is 0.0 to 1.0

    Returns:
        DebateResult with all debate data
    """
    start_time = time.time()

    # Clear per-session caches for fresh debate
    self._clear_session_caches()

    # STEP 1: Topic Analysis
    self._report_progress("Topic Analysis", 0.05, progress_callback)
    topic_analysis = analyze_topic(topic)
    corrected_topic = topic_analysis.corrected_topic

    # STEP 2: Research Gathering
    self._report_progress("Research", 0.15, progress_callback)
    research_context = self._gather_research_with_queries(
        topic_analysis.research_queries,
        corrected_topic,
    )

    # STEP 3: Research Classification
    self._report_progress("Analyzing Research", 0.25, progress_callback)
    classified_research = analyze_research(research_context, corrected_topic)

    # Format research for each debater
    pro_context = format_for_debater(classified_research, "pro")
    con_context = format_for_debater(classified_research, "con")

    # STEP 4: Domain Classification
    domain = topic_analysis.domain_hint or "debate"

    # Load domain adapters
    self.model_manager.load_adapter("pro", domain)
    self.model_manager.load_adapter("con", domain)

    # STEP 5: TV Host Introduction
    self._report_progress("Host Introduction", 0.30, progress_callback)
    host_intro = generate_tv_host_introduction(
        topic=corrected_topic,
        research=classified_research,
    )

    # STEP 6: Debate Rounds
    pro_arguments = []
    con_arguments = []

    for round_num in range(1, num_rounds + 1):
        progress = 0.30 + (0.40 * round_num / num_rounds)
        self._report_progress(f"Round {round_num}", progress, progress_callback)

        # Pro turn
        pro_arg = self._generate_argument(
            topic=corrected_topic,
            domain=domain,
            stance="pro",
            research_context=pro_context,
            round_num=round_num,
        )
        pro_arguments.append(pro_arg)

        # Add Pro's turn to Con's history (for awareness)
        self.con_debate_tool.add_external_turn("pro", pro_arg, round_num)

        # Con turn
        con_arg = self._generate_argument(
            topic=corrected_topic,
            domain=domain,
            stance="con",
            research_context=con_context,
            round_num=round_num,
        )
        con_arguments.append(con_arg)

        # Add Con's turn to Pro's history (for next round)
        self.pro_debate_tool.add_external_turn("con", con_arg, round_num)

    # STEP 7: Fact-Checking
    self._report_progress("Fact-Checking", 0.75, progress_callback)
    fact_check = self._fact_check_debate(
        pro_arguments=pro_arguments,
        con_arguments=con_arguments,
        research_context=research_context,
    )

    # STEP 8: Judging
    self._report_progress("Judging", 0.85, progress_callback)
    judge_score = judge_debate(
        pro_arguments=pro_arguments,
        con_arguments=con_arguments,
        fact_check_results=fact_check,
    )

    # STEP 9: Guest Recommendations (Optional)
    recommended_guests = []
    if recommend_guests:
        self._report_progress("Finding Guests", 0.90, progress_callback)
        recommended_guests = recommend_debate_guests(
            topic=corrected_topic,
            domain=domain,
            wikipedia_tool=self.wikipedia_tool,
            internet_tool=self.internet_tool if self.use_internet else None,
        )

    # Build result
    duration = time.time() - start_time

    result = DebateResult(
        topic=corrected_topic,
        domain=domain,
        rounds=num_rounds,
        pro_arguments=pro_arguments,
        con_arguments=con_arguments,
        research_context=research_context,
        host_introduction=host_intro.opening if host_intro else "",
        fact_check=fact_check,
        judge_score=judge_score,
        recommended_guests=recommended_guests,
        duration_seconds=duration,
        use_internet=self.use_internet,
    )

    # Save artifacts
    self._report_progress("Saving", 0.95, progress_callback)
    self._save_artifacts(result)

    self._report_progress("Complete", 1.0, progress_callback)
    return result
```

### 2.4 Research Gathering

```python
def _gather_research_with_queries(
    self,
    queries: list[str],
    topic: str,
) -> str:
    """
    Execute research queries and combine results.

    Args:
        queries: List of search queries from topic analysis
        topic: Original topic for context

    Returns:
        Combined research text
    """
    research_parts = []

    # Always search Wikipedia
    for query in queries[:3]:  # Top 3 queries for Wikipedia
        try:
            wiki_result = self.wikipedia_tool._run(
                query=query,
                search_type="summary",
                sentences=5,
            )
            if wiki_result and len(wiki_result) > 50:
                research_parts.append(f"[Wikipedia] {wiki_result}")
        except Exception as e:
            if self.verbose:
                print(f"  Wikipedia search failed for '{query}': {e}")

    # Internet search if enabled
    if self.use_internet:
        for query in queries[:4]:  # Top 4 queries for internet
            try:
                internet_result = self.internet_tool._run(
                    topic=query,
                    search_type="debate",
                )
                if internet_result and len(internet_result) > 50:
                    research_parts.append(f"[Web] {internet_result}")
            except Exception as e:
                if self.verbose:
                    print(f"  Internet search failed for '{query}': {e}")

    # Combine and deduplicate
    combined = "\n\n".join(research_parts)

    # Truncate if too long (context limit)
    max_chars = 8000
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "..."

    return combined
```

### 2.5 Argument Generation

```python
def _generate_argument(
    self,
    topic: str,
    domain: str,
    stance: str,
    research_context: str,
    round_num: int,
) -> str:
    """
    Generate a single debate argument.

    Args:
        topic: Debate topic
        domain: Domain for adapter selection
        stance: "pro" or "con"
        research_context: Stance-specific research
        round_num: Current round number

    Returns:
        Generated argument string
    """
    tool = self.pro_debate_tool if stance == "pro" else self.con_debate_tool

    argument = tool._run(
        topic=topic,
        stance=stance,
        domain=domain,
        research_context=research_context,
        round_num=round_num,
    )

    return argument
```

### 2.6 Fact-Checking

```python
def _fact_check_debate(
    self,
    pro_arguments: list[str],
    con_arguments: list[str],
    research_context: str,
) -> dict:
    """
    Fact-check both sides of the debate.

    Args:
        pro_arguments: All Pro arguments
        con_arguments: All Con arguments
        research_context: Original research for verification

    Returns:
        Dict with pro/con fact-check results
    """
    # Combine all arguments per side
    pro_combined = " ".join(pro_arguments)
    con_combined = " ".join(con_arguments)

    # Compute faithfulness scores
    pro_result = compute_faithfulness_score(pro_combined, research_context)
    con_result = compute_faithfulness_score(con_combined, research_context)

    return {
        "pro": pro_result,
        "con": con_result,
    }
```

### 2.7 Artifact Saving

```python
def _save_artifacts(self, result: DebateResult) -> Path:
    """
    Save debate results to files.

    Args:
        result: Complete debate result

    Returns:
        Path to output directory
    """
    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic_slug = re.sub(r"[^a-z0-9]+", "_", result.topic.lower())[:30]
    output_path = self.output_dir / f"{timestamp}_{topic_slug}"
    output_path.mkdir(parents=True, exist_ok=True)

    # Save JSON result
    result_json = {
        "topic": result.topic,
        "domain": result.domain,
        "rounds": result.rounds,
        "pro_arguments": result.pro_arguments,
        "con_arguments": result.con_arguments,
        "research_context": result.research_context,
        "host_introduction": result.host_introduction,
        "fact_check": result.fact_check,
        "judge_score": {
            "pro_score": result.judge_score.pro_score,
            "con_score": result.judge_score.con_score,
            "winner": result.judge_score.winner,
            "reasoning": result.judge_score.reasoning,
        } if result.judge_score else None,
        "recommended_guests": [
            {
                "name": g.name,
                "title": g.title,
                "expertise": g.expertise,
                "relevance": g.relevance,
            }
            for g in result.recommended_guests
        ],
        "duration_seconds": result.duration_seconds,
        "use_internet": result.use_internet,
        "timestamp": timestamp,
    }

    with open(output_path / "result.json", "w") as f:
        json.dump(result_json, f, indent=2)

    # Save human-readable transcript
    transcript = self._format_transcript(result)
    with open(output_path / "transcript.txt", "w") as f:
        f.write(transcript)

    if self.verbose:
        print(f"Results saved to: {output_path}")

    return output_path
```

### 2.8 DebateResult Dataclass

```python
@dataclass
class DebateResult:
    """Complete result of a debate."""

    topic: str                              # Corrected topic
    domain: str                             # Detected domain
    rounds: int                             # Number of rounds
    pro_arguments: list[str]                # One per round
    con_arguments: list[str]                # One per round
    research_context: str                   # Combined research
    host_introduction: str                  # TV host opening
    fact_check: dict                        # {pro, con} with scores
    judge_score: Optional[JudgeScore]       # Final scoring
    recommended_guests: list[DebateGuest]   # Expert recommendations
    duration_seconds: float                 # Total execution time
    use_internet: bool                      # Was internet used
```

---

## 3. DUALMODELMANAGER - TWO LLM INSTANCES

**File**: `src/crew/utils/dual_model_manager.py` (277 lines)

### 3.1 Design Philosophy

The dual model architecture ensures:

1. **True Independence**: Pro and Con have separate model instances
2. **No Context Bleeding**: Each model maintains its own KV cache
3. **Parallel Potential**: Could theoretically run on different GPUs
4. **Adapter Isolation**: Each model can load different domain adapters

### 3.2 Class Definition

```python
class DualModelManager:
    """
    Manages two independent LLM instances for Pro and Con debaters.

    This allows true parallel thinking without context contamination
    between the two sides of the debate.
    """

    def __init__(
        self,
        base_model_path: Path | str | None = None,
        device_map: str = "auto",
    ):
        """
        Initialize manager (models loaded lazily).

        Args:
            base_model_path: Path to base model (default: project models/base)
            device_map: Device mapping for model loading
        """
        self.base_model_path = base_model_path or BASE_MODEL_PATH
        self.device_map = device_map

        # Lazy-loaded models
        self._model_pro: AutoModelForCausalLM | None = None
        self._model_con: AutoModelForCausalLM | None = None
        self._tokenizer: AutoTokenizer | None = None

        # Track current adapters
        self.current_adapter_pro: str | None = None
        self.current_adapter_con: str | None = None
```

### 3.3 Model Loading

```python
@property
def model_pro(self) -> AutoModelForCausalLM:
    """Lazy-load Pro model instance."""
    if self._model_pro is None:
        print("Loading Pro model instance...")
        self._model_pro, self._tokenizer = load_base_model(
            model_path=self.base_model_path,
            device_map=self.device_map,
        )
        print(f"  Pro model loaded. VRAM: {self._get_model_vram(self._model_pro):.2f} GB")
    return self._model_pro

@property
def model_con(self) -> AutoModelForCausalLM:
    """Lazy-load Con model instance."""
    if self._model_con is None:
        print("Loading Con model instance...")
        # Load completely separate instance
        self._model_con, _ = load_base_model(
            model_path=self.base_model_path,
            device_map=self.device_map,
        )
        print(f"  Con model loaded. VRAM: {self._get_model_vram(self._model_con):.2f} GB")
    return self._model_con

@property
def tokenizer(self) -> AutoTokenizer:
    """Get tokenizer (shared between models)."""
    if self._tokenizer is None:
        # Force model_pro load to get tokenizer
        _ = self.model_pro
    return self._tokenizer
```

### 3.4 Dynamic Adapter Loading

```python
def load_adapter(
    self,
    model_key: str,
    domain: str,
) -> bool:
    """
    Load a domain-specific adapter onto a model.

    Args:
        model_key: "pro" or "con"
        domain: Domain name (education, medicine, ecology, etc.)

    Returns:
        True if adapter loaded, False if reverted to base
    """
    # Get model reference
    if model_key == "pro":
        model = self.model_pro
        current = self.current_adapter_pro
    else:
        model = self.model_con
        current = self.current_adapter_con

    # Skip if already loaded
    if current == domain:
        return True

    # Find adapter path
    adapter_path = ADAPTERS_PATH / domain

    if not adapter_path.exists():
        print(f"  Adapter '{domain}' not found, using base model")
        self._unload_adapter(model_key)
        return False

    # Load adapter
    try:
        print(f"  Loading '{domain}' adapter for {model_key}...")

        # First unload any existing adapter
        self._unload_adapter(model_key)

        # Load new adapter
        model = PeftModel.from_pretrained(
            model,
            adapter_path,
            is_trainable=False,
        )

        # Update reference
        if model_key == "pro":
            self._model_pro = model
            self.current_adapter_pro = domain
        else:
            self._model_con = model
            self.current_adapter_con = domain

        print(f"    Adapter loaded successfully")
        return True

    except Exception as e:
        print(f"  Failed to load adapter: {e}")
        return False

def _unload_adapter(self, model_key: str):
    """Remove adapter and revert to base model."""
    if model_key == "pro" and self.current_adapter_pro:
        # PEFT models can be merged or unloaded
        if hasattr(self._model_pro, "unload"):
            self._model_pro.unload()
        self.current_adapter_pro = None
    elif model_key == "con" and self.current_adapter_con:
        if hasattr(self._model_con, "unload"):
            self._model_con.unload()
        self.current_adapter_con = None
```

### 3.5 Text Generation

```python
def generate_pro(
    self,
    prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
) -> str:
    """
    Generate text using Pro model.

    Args:
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 = deterministic)
        top_p: Nucleus sampling threshold
        do_sample: Enable sampling (vs greedy)

    Returns:
        Generated text
    """
    return self._generate(
        model=self.model_pro,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=do_sample,
    )

def generate_con(
    self,
    prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
) -> str:
    """Generate text using Con model."""
    return self._generate(
        model=self.model_con,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=do_sample,
    )

def _generate(
    self,
    model: AutoModelForCausalLM,
    prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    do_sample: bool,
) -> str:
    """Internal generation method."""
    # Tokenize
    inputs = self.tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
    ).to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=self.tokenizer.eos_token_id,
        )

    # Decode (skip input tokens)
    generated = self.tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    )

    return generated.strip()
```

### 3.6 Memory Statistics

```python
def get_memory_stats(self) -> dict:
    """
    Get GPU memory usage statistics.

    Returns:
        Dict with memory info per model
    """
    stats = {
        "pro_loaded": self._model_pro is not None,
        "con_loaded": self._model_con is not None,
        "pro_adapter": self.current_adapter_pro,
        "con_adapter": self.current_adapter_con,
    }

    if torch.cuda.is_available():
        stats["gpu_allocated_gb"] = torch.cuda.memory_allocated() / 1e9
        stats["gpu_reserved_gb"] = torch.cuda.memory_reserved() / 1e9
        stats["gpu_total_gb"] = torch.cuda.get_device_properties(0).total_memory / 1e9

    return stats

def _get_model_vram(self, model: AutoModelForCausalLM) -> float:
    """Estimate VRAM used by a model."""
    param_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    return param_bytes / 1e9
```

---

## 4. ALL 11 CREWAI AGENTS

### 4.1 Topic Analyst Agent

**File**: `src/crew/agents/topic_analyst.py`

**Purpose**: Grammar correction, key term extraction, domain detection, and query generation.

```python
@dataclass
class TopicAnalysis:
    """Result of topic analysis."""
    original_topic: str              # Raw user input
    corrected_topic: str             # Grammar-corrected version
    research_queries: list[str]      # 6 optimized search queries
    persona_queries: list[str]       # Queries for finding experts
    key_terms: list[str]             # Extracted keywords (max 6)
    domain_hint: str                 # Detected domain
    is_well_formed: bool             # Was input valid

# Common misspellings
GRAMMAR_CORRECTIONS = {
    "eletric": "electric",
    "vehicals": "vehicles",
    "goverment": "government",
    "enviornment": "environment",
    "recieve": "receive",
    "occured": "occurred",
    "seperate": "separate",
    "definately": "definitely",
    "accomodate": "accommodate",
    "occurence": "occurrence",
    "independant": "independent",
    "neccessary": "necessary",
    "priviledge": "privilege",
    "refered": "referred",
    "untill": "until",
    "writting": "writing",
    "beleive": "believe",
    "existance": "existence",
    "millenium": "millennium",
    "publically": "publicly",
}

# Domain keyword mapping
DOMAIN_KEYWORDS = {
    "economics": ["economy", "market", "trade", "gdp", "inflation", "tax", "budget", "fiscal"],
    "environment": ["climate", "pollution", "carbon", "emission", "renewable", "fossil", "green"],
    "technology": ["ai", "artificial intelligence", "robot", "automation", "digital", "cyber", "software"],
    "healthcare": ["health", "medical", "hospital", "doctor", "disease", "treatment", "vaccine"],
    "education": ["school", "university", "student", "teacher", "curriculum", "learning", "college"],
    "politics": ["government", "election", "democracy", "vote", "congress", "senate", "policy"],
    "energy": ["oil", "gas", "nuclear", "solar", "wind", "electricity", "power grid"],
    "social": ["society", "community", "family", "culture", "equality", "diversity", "rights"],
}

def analyze_topic(topic: str) -> TopicAnalysis:
    """
    Analyze a debate topic comprehensively.

    Args:
        topic: Raw user input

    Returns:
        TopicAnalysis with all extracted information
    """
    # Step 1: Grammar correction
    corrected = topic
    for wrong, right in GRAMMAR_CORRECTIONS.items():
        corrected = re.sub(rf"\b{wrong}\b", right, corrected, flags=re.IGNORECASE)

    # Step 2: Extract key terms
    # Remove stopwords and common words
    stopwords = {"should", "be", "the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "for"}
    words = corrected.lower().split()
    key_terms = [w for w in words if w not in stopwords and len(w) > 2][:6]

    # Step 3: Detect domain
    domain_scores = {}
    topic_lower = corrected.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in topic_lower)
        if score > 0:
            domain_scores[domain] = score

    domain_hint = "general"
    if domain_scores:
        domain_hint = max(domain_scores, key=domain_scores.get)

    # Step 4: Generate research queries
    year = datetime.now().year
    research_queries = [
        f"{corrected} debate {year}",
        f"{' '.join(key_terms[:3])} benefits advantages",
        f"{' '.join(key_terms[:3])} problems concerns risks",
        f"{' '.join(key_terms[:3])} statistics data facts",
        f"{' '.join(key_terms[:3])} expert opinion analysis",
        f"{' '.join(key_terms[:3])} arguments for against",
    ]

    # Step 5: Generate persona queries
    persona_queries = [
        f"{domain_hint} expert {' '.join(key_terms[:2])}",
        f"{' '.join(key_terms[:2])} researcher professor",
        f"{' '.join(key_terms[:2])} policy analyst",
    ]

    return TopicAnalysis(
        original_topic=topic,
        corrected_topic=corrected,
        research_queries=research_queries,
        persona_queries=persona_queries,
        key_terms=key_terms,
        domain_hint=domain_hint,
        is_well_formed=len(words) >= 3,  # At least 3 words
    )
```

### 4.2 Research Analyst Agent

**File**: `src/crew/agents/research_analyst.py`

**Purpose**: Classify raw research into PRO/CON categories.

```python
@dataclass
class ClassifiedResearch:
    """Research organized by argument type."""
    topic: str
    pro_points: list[str]          # Supporting evidence (3-5 points)
    con_points: list[str]          # Opposing evidence (3-5 points)
    key_facts: list[str]           # Neutral facts
    statistics: list[str]          # Numbers and data
    sources: list[str]             # Source URLs/references
    quality_score: int             # 0-100 overall quality

# Indicator words for classification
PRO_INDICATORS = [
    "benefit", "advantage", "positive", "improve", "success",
    "effective", "efficient", "growth", "opportunity", "support",
]

CON_INDICATORS = [
    "problem", "risk", "negative", "concern", "issue",
    "challenge", "drawback", "failure", "cost", "danger",
]

FACT_INDICATORS = [
    "according to", "research shows", "study found", "data indicates",
    "statistics show", "evidence suggests", "report states",
]

def analyze_research(research_text: str, topic: str) -> ClassifiedResearch:
    """
    Classify research text into structured categories.

    Args:
        research_text: Raw research from Wikipedia/internet
        topic: Original topic for context

    Returns:
        ClassifiedResearch with organized points
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', research_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    pro_points = []
    con_points = []
    key_facts = []
    statistics = []

    for sentence in sentences:
        sentence_lower = sentence.lower()

        # Check for statistics (numbers + units)
        if re.search(r'\d+\s*(%|percent|million|billion|thousand)', sentence_lower):
            statistics.append(sentence)
            continue

        # Check for facts
        if any(indicator in sentence_lower for indicator in FACT_INDICATORS):
            key_facts.append(sentence)
            continue

        # Count pro/con indicators
        pro_score = sum(1 for ind in PRO_INDICATORS if ind in sentence_lower)
        con_score = sum(1 for ind in CON_INDICATORS if ind in sentence_lower)

        if pro_score > con_score and pro_score > 0:
            pro_points.append(sentence)
        elif con_score > pro_score and con_score > 0:
            con_points.append(sentence)

    # Limit to top 5 each
    pro_points = pro_points[:5]
    con_points = con_points[:5]
    key_facts = key_facts[:5]
    statistics = statistics[:5]

    # Calculate quality score
    quality_score = _calculate_quality_score(
        pro_points, con_points, key_facts, statistics
    )

    return ClassifiedResearch(
        topic=topic,
        pro_points=pro_points,
        con_points=con_points,
        key_facts=key_facts,
        statistics=statistics,
        sources=[],  # Populated from search metadata
        quality_score=quality_score,
    )

def _calculate_quality_score(
    pro_points: list[str],
    con_points: list[str],
    key_facts: list[str],
    statistics: list[str],
) -> int:
    """Calculate research quality score (0-100)."""
    score = 0

    # Balance (both sides represented): 0-30 points
    balance = min(len(pro_points), len(con_points))
    score += min(30, balance * 10)

    # Specificity (statistics present): 0-25 points
    score += min(25, len(statistics) * 5)

    # Facts (neutral facts present): 0-25 points
    score += min(25, len(key_facts) * 5)

    # Breadth (total points): 0-20 points
    total = len(pro_points) + len(con_points)
    score += min(20, total * 2)

    return min(100, score)

def format_for_debater(research: ClassifiedResearch, stance: str) -> str:
    """
    Format research for a specific debater stance.

    Args:
        research: Classified research object
        stance: "pro" or "con"

    Returns:
        Formatted research context string
    """
    parts = []

    if stance == "pro":
        parts.append("SUPPORTING EVIDENCE:")
        for point in research.pro_points:
            parts.append(f"• {point}")
        parts.append("\nCOUNTER-ARGUMENTS TO ADDRESS:")
        for point in research.con_points[:2]:  # Only top 2 con points
            parts.append(f"• {point}")
    else:
        parts.append("SUPPORTING EVIDENCE:")
        for point in research.con_points:
            parts.append(f"• {point}")
        parts.append("\nCOUNTER-ARGUMENTS TO ADDRESS:")
        for point in research.pro_points[:2]:  # Only top 2 pro points
            parts.append(f"• {point}")

    if research.statistics:
        parts.append("\nKEY STATISTICS:")
        for stat in research.statistics[:3]:
            parts.append(f"• {stat}")

    return "\n".join(parts)
```

### 4.3 Router Agent

**File**: `src/crew/agents/router_agent.py`

**Purpose**: Classify debate topics into domains for adapter selection.

```python
from crewai import Agent

# Domain keywords (expanded)
DOMAIN_KEYWORDS = {
    "education": [
        "school", "university", "student", "teacher", "curriculum",
        "learning", "college", "degree", "education", "academic",
        "classroom", "homework", "tuition", "scholarship", "professor",
    ],
    "medicine": [
        "health", "medical", "hospital", "doctor", "disease",
        "treatment", "vaccine", "patient", "surgery", "diagnosis",
        "pharmaceutical", "clinical", "therapy", "symptom", "cure",
    ],
    "ecology": [
        "environment", "climate", "pollution", "ecosystem", "biodiversity",
        "conservation", "species", "habitat", "wildlife", "nature",
        "deforestation", "extinction", "carbon", "sustainability", "green",
    ],
    "technology": [
        "ai", "artificial intelligence", "robot", "automation", "digital",
        "software", "hardware", "internet", "computer", "algorithm",
        "machine learning", "data", "cyber", "innovation", "tech",
    ],
    "debate": [  # General fallback
        "should", "argue", "opinion", "controversial", "debate",
    ],
}

def create_router_agent() -> Agent:
    """Create a domain classification agent."""
    return Agent(
        role="Domain Router",
        goal="Classify debate topics into the most appropriate domain category",
        backstory="""You are an expert at categorizing discussion topics.
        You understand the nuances between different fields like education,
        medicine, technology, and environmental science. Your classifications
        help route debates to specialists with domain expertise.""",
        verbose=False,
        allow_delegation=False,
    )

def classify_domain(topic: str) -> tuple[str, float]:
    """
    Classify a topic into a domain.

    Args:
        topic: Debate topic string

    Returns:
        Tuple of (domain_name, confidence_score)
    """
    topic_lower = topic.lower()

    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in topic_lower)
        if score > 0:
            scores[domain] = score

    if not scores:
        return ("debate", 0.0)

    best_domain = max(scores, key=scores.get)
    confidence = scores[best_domain] / len(DOMAIN_KEYWORDS[best_domain])

    return (best_domain, min(1.0, confidence))
```

### 4.4 Debater Agents (Pro & Con)

**File**: `src/crew/agents/debater_agents.py`

**Purpose**: Generate compelling arguments for each side.

```python
from crewai import Agent
from src.crew.tools.debate_tool import DebateGenerationTool

def create_pro_debater_agent(debate_tool: DebateGenerationTool) -> Agent:
    """
    Create the Pro debater agent.

    Args:
        debate_tool: Configured debate generation tool for Pro

    Returns:
        CrewAI Agent for Pro side
    """
    return Agent(
        role="Pro Debater",
        goal="""Construct compelling arguments IN FAVOR of the debate topic.
        Your goal is to WIN the audience to your side through persuasion,
        evidence, and rhetorical skill. Keep responses concise: 5 sentences
        (maximum 8 if absolutely critical).""",
        backstory="""You are a skilled advocate who excels at building
        persuasive cases for any position. You combine logical reasoning
        with emotional appeal. You understand how to use evidence effectively
        and how to anticipate and counter opposing arguments. You speak
        naturally and passionately, like a human advocate at a live debate,
        NOT like an AI assistant.""",
        tools=[debate_tool],
        verbose=False,
        allow_delegation=False,
    )

def create_con_debater_agent(debate_tool: DebateGenerationTool) -> Agent:
    """
    Create the Con debater agent.

    Args:
        debate_tool: Configured debate generation tool for Con

    Returns:
        CrewAI Agent for Con side
    """
    return Agent(
        role="Con Debater",
        goal="""Construct compelling arguments AGAINST the debate topic.
        Your goal is to WIN the audience to your side by exposing flaws
        in the opposing argument and presenting superior alternatives.
        Keep responses concise: 5 sentences (maximum 8 if absolutely critical).""",
        backstory="""You are a skilled critic and skeptic who excels at
        identifying weaknesses in arguments and presenting compelling
        counterpoints. You combine careful analysis with persuasive
        rhetoric. You speak naturally and confidently, like a seasoned
        debater at a live event, NOT like an AI assistant.""",
        tools=[debate_tool],
        verbose=False,
        allow_delegation=False,
    )
```

### 4.5 Fact-Check Agent

**File**: `src/crew/agents/factcheck_agent.py`

**Purpose**: Verify argument accuracy against research.

```python
from crewai import Agent

# Stopwords for claim extraction
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "this", "that", "these", "those", "i", "you",
    "he", "she", "it", "we", "they", "what", "which", "who", "whom", "whose",
}

def create_factcheck_agent() -> Agent:
    """Create fact-checking agent."""
    return Agent(
        role="Fact Checker",
        goal="Verify the accuracy of claims made during the debate",
        backstory="""You are a meticulous fact-checker with expertise in
        verifying claims against source material. You identify unsupported
        assertions, check statistical accuracy, and evaluate the overall
        faithfulness of arguments to the evidence.""",
        verbose=False,
        allow_delegation=False,
    )

def compute_faithfulness_score(
    argument: str,
    research_context: str,
) -> dict:
    """
    Compute how well an argument is supported by research.

    Uses keyword overlap (Jaccard-like similarity) to estimate
    how many claims are grounded in the research.

    Args:
        argument: Debate argument text
        research_context: Research text to verify against

    Returns:
        Dict with scoring metrics
    """
    # Extract claims (sentences with substance)
    claims = _extract_claims(argument)

    if not claims:
        return {
            "num_claims": 0,
            "supported_claims": 0,
            "avg_support_score": 0.0,
            "faithfulness_score": 0.0,
            "verdict": "no_claims",
        }

    # Tokenize research for comparison
    research_words = _tokenize(research_context)

    # Score each claim
    claim_scores = []
    supported_count = 0

    for claim in claims:
        claim_words = _tokenize(claim)

        if not claim_words:
            continue

        # Calculate overlap
        overlap = len(claim_words & research_words)
        score = overlap / max(len(claim_words), 1)
        claim_scores.append(score)

        if score >= 0.3:  # Threshold for "supported"
            supported_count += 1

    # Aggregate
    avg_score = sum(claim_scores) / len(claim_scores) if claim_scores else 0.0
    faithfulness = supported_count / len(claims) if claims else 0.0

    # Determine verdict
    if faithfulness >= 0.7:
        verdict = "well_supported"
    elif faithfulness >= 0.4:
        verdict = "partially_supported"
    else:
        verdict = "weakly_supported"

    return {
        "num_claims": len(claims),
        "supported_claims": supported_count,
        "avg_support_score": round(avg_score, 3),
        "faithfulness_score": round(faithfulness, 3),
        "verdict": verdict,
    }

def _extract_claims(text: str) -> list[str]:
    """Extract substantive claims from text."""
    sentences = re.split(r'[.!?]+', text)
    claims = []

    for sentence in sentences:
        sentence = sentence.strip()
        words = sentence.split()

        # Require at least 5 words for a claim
        if len(words) >= 5:
            claims.append(sentence)

    return claims

def _tokenize(text: str) -> set[str]:
    """Tokenize text into word set (lowercase, no stopwords)."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}
```

### 4.6 Judge Agent

**File**: `src/crew/agents/judge_agent.py`

**Purpose**: Score arguments and determine winner.

```python
from dataclasses import dataclass
from crewai import Agent

@dataclass
class JudgeScore:
    """Final debate judgment."""
    pro_score: int          # 0-100
    con_score: int          # 0-100
    winner: str             # "pro", "con", or "tie"
    reasoning: str          # Explanation of decision

# Scoring indicators
LOGIC_MARKERS = [
    "because", "therefore", "thus", "consequently", "since",
    "as a result", "hence", "so", "given that", "due to",
]

EVIDENCE_MARKERS = [
    "study", "research", "data", "percent", "%", "according to",
    "expert", "scientist", "professor", "report", "survey",
    "statistics", "evidence", "found that", "shows that",
]

AGGRESSIVE_WORDS = [
    "stupid", "idiot", "nonsense", "ridiculous", "absurd",
    "moron", "fool", "ignorant", "dumb", "pathetic",
]

def create_judge_agent() -> Agent:
    """Create the judge agent."""
    return Agent(
        role="Debate Judge",
        goal="Fairly evaluate debate arguments and determine a winner",
        backstory="""You are an experienced debate judge with expertise
        in evaluating argumentation quality. You assess logic, evidence,
        rhetoric, and civility. You are fair and impartial, basing your
        decisions solely on the quality of arguments presented.""",
        verbose=False,
        allow_delegation=False,
    )

def judge_debate(
    pro_arguments: list[str],
    con_arguments: list[str],
    fact_check_results: dict = None,
) -> JudgeScore:
    """
    Judge the debate and determine winner.

    Args:
        pro_arguments: All Pro side arguments
        con_arguments: All Con side arguments
        fact_check_results: Optional fact-check scores

    Returns:
        JudgeScore with final decision
    """
    # Score each argument
    pro_scores = [_score_argument(arg) for arg in pro_arguments]
    con_scores = [_score_argument(arg) for arg in con_arguments]

    # Average scores
    pro_avg = sum(pro_scores) / len(pro_scores) if pro_scores else 0
    con_avg = sum(con_scores) / len(con_scores) if con_scores else 0

    # Apply fact-check weight (30%)
    if fact_check_results:
        pro_faith = fact_check_results.get("pro", {}).get("faithfulness_score", 0.5)
        con_faith = fact_check_results.get("con", {}).get("faithfulness_score", 0.5)

        pro_final = pro_avg * 0.7 + (pro_faith * 100) * 0.3
        con_final = con_avg * 0.7 + (con_faith * 100) * 0.3
    else:
        pro_final = pro_avg
        con_final = con_avg

    # Round to integers
    pro_final = int(round(pro_final))
    con_final = int(round(con_final))

    # Determine winner
    margin = abs(pro_final - con_final)

    if margin < 3:
        winner = "tie"
        reasoning = f"The debate ends in a tie. Both sides presented comparable arguments with similar quality (Pro: {pro_final}, Con: {con_final})."
    elif pro_final > con_final:
        winner = "pro"
        reasoning = f"Pro wins with a score of {pro_final} to {con_final}. "
        if fact_check_results and pro_faith > con_faith:
            reasoning += "Pro's arguments were better supported by evidence. "
        reasoning += "Pro demonstrated stronger argumentation overall."
    else:
        winner = "con"
        reasoning = f"Con wins with a score of {con_final} to {pro_final}. "
        if fact_check_results and con_faith > pro_faith:
            reasoning += "Con's arguments were better supported by evidence. "
        reasoning += "Con demonstrated stronger argumentation overall."

    return JudgeScore(
        pro_score=pro_final,
        con_score=con_final,
        winner=winner,
        reasoning=reasoning,
    )

def _score_argument(argument: str) -> int:
    """
    Score a single argument (0-100).

    Criteria:
    - Length (0-25): Word count normalized
    - Logic (0-25): Presence of logical markers
    - Evidence (0-25): Citations and data references
    - Civility (0-25): Absence of aggressive language
    """
    arg_lower = argument.lower()
    words = argument.split()

    # Length score (0-25)
    # Target: 50-100 words
    word_count = len(words)
    length_score = min(25, word_count * 25 / 100)

    # Logic score (0-25)
    logic_count = sum(1 for marker in LOGIC_MARKERS if marker in arg_lower)
    logic_score = min(25, logic_count * 5)

    # Evidence score (0-25)
    evidence_count = sum(1 for marker in EVIDENCE_MARKERS if marker in arg_lower)
    evidence_score = min(25, evidence_count * 5)

    # Civility score (0-25)
    aggressive_count = sum(1 for word in AGGRESSIVE_WORDS if word in arg_lower)
    civility_score = max(0, 25 - aggressive_count * 10)

    total = int(length_score + logic_score + evidence_score + civility_score)
    return min(100, total)
```

### 4.7 Persona Agent

**File**: `src/crew/agents/persona_agent.py`

**Purpose**: Recommend real experts for debate panels.

```python
from dataclasses import dataclass
from crewai import Agent

@dataclass
class DebateGuest:
    """A recommended debate guest."""
    name: str               # Full name
    title: str              # Professional title
    expertise: str          # Area of expertise
    relevance: str          # Why relevant to this debate

# Person indicators in bios
PERSON_INDICATORS = [
    "born", "is a", "was a", "professor", "scientist", "researcher",
    "economist", "author", "journalist", "analyst", "expert",
    "he was", "she was", "graduated", "studied at", "works at",
]

# Non-person indicators
NOT_PERSON_INDICATORS = [
    "is the name of", "refers to", "is a policy", "is a term",
    "is a company", "is an organization", "is a movement",
    "is a concept", "is a theory", "is a type of",
]

def create_persona_agent() -> Agent:
    """Create persona recommendation agent."""
    return Agent(
        role="Guest Booker",
        goal="Find relevant experts who could contribute to the debate",
        backstory="""You are a TV producer with expertise in finding
        the perfect guests for debate shows. You know how to identify
        real experts with genuine credentials and relevant perspectives
        on any topic.""",
        verbose=False,
        allow_delegation=False,
    )

def recommend_debate_guests(
    topic: str,
    domain: str,
    wikipedia_tool,
    internet_tool=None,
    num_guests: int = 4,
) -> list[DebateGuest]:
    """
    Find real experts relevant to the debate topic.

    Args:
        topic: Debate topic
        domain: Topic domain
        wikipedia_tool: Wikipedia search tool
        internet_tool: Optional internet search tool
        num_guests: Number of guests to recommend

    Returns:
        List of DebateGuest recommendations
    """
    guests = []
    seen_names = set()

    # Generate search queries
    queries = _generate_expert_queries(topic, domain)

    for query in queries:
        if len(guests) >= num_guests:
            break

        try:
            # Search Wikipedia for experts
            result = wikipedia_tool._run(
                query=query,
                search_type="experts",
            )

            if not result:
                continue

            # Parse potential experts from result
            potential = _parse_experts(result, topic)

            for expert in potential:
                if expert.name not in seen_names:
                    # Validate it's a real person
                    if _is_real_person(expert.name, wikipedia_tool):
                        guests.append(expert)
                        seen_names.add(expert.name)

                        if len(guests) >= num_guests:
                            break

        except Exception:
            continue

    return guests

def _generate_expert_queries(topic: str, domain: str) -> list[str]:
    """Generate queries to find experts."""
    # Extract key terms
    words = topic.lower().split()
    key_terms = " ".join(w for w in words if len(w) > 3)[:50]

    queries = [
        f"{domain} expert {key_terms}",
        f"{key_terms} professor researcher",
        f"{key_terms} economist analyst",  # For policy topics
        f"{key_terms} scientist author",
        f"{key_terms} advocate critic",
    ]

    return queries

def _parse_experts(wiki_text: str, topic: str) -> list[DebateGuest]:
    """Parse potential experts from Wikipedia text."""
    experts = []

    # Look for name patterns (simplified)
    # Real implementation would use NER
    lines = wiki_text.split("\n")

    for line in lines:
        # Check for person indicators
        if any(ind in line.lower() for ind in PERSON_INDICATORS):
            # Try to extract name (first capitalized words)
            words = line.split()
            name_words = []

            for word in words[:5]:
                if word[0].isupper() and word.isalpha():
                    name_words.append(word)
                elif name_words:
                    break

            if len(name_words) >= 2:
                name = " ".join(name_words)

                # Extract title (text after "is a" or "was a")
                title = "Expert"
                if " is a " in line:
                    title = line.split(" is a ")[1].split(".")[0][:50]
                elif " was a " in line:
                    title = line.split(" was a ")[1].split(".")[0][:50]

                experts.append(DebateGuest(
                    name=name,
                    title=title.strip(),
                    expertise=topic[:50],
                    relevance=f"Expert on {topic[:30]}",
                ))

    return experts[:3]  # Limit per query

def _is_real_person(name: str, wikipedia_tool) -> bool:
    """Verify name refers to a real person."""
    try:
        result = wikipedia_tool._run(
            query=name,
            search_type="summary",
            sentences=2,
        )

        if not result:
            return False

        result_lower = result.lower()

        # Check for non-person indicators
        if any(ind in result_lower for ind in NOT_PERSON_INDICATORS):
            return False

        # Check for person indicators
        return any(ind in result_lower for ind in PERSON_INDICATORS)

    except Exception:
        return False
```

### 4.8 TV Host Agent

**File**: `src/crew/agents/tv_host_agent.py`

**Purpose**: Generate engaging debate introductions.

```python
from dataclasses import dataclass
from crewai import Agent

@dataclass
class DebateIntroduction:
    """TV host debate introduction."""
    opening: str                    # Welcome message
    key_questions: list[str]        # Questions for the debate

def create_tv_host_agent() -> Agent:
    """Create TV host agent."""
    return Agent(
        role="TV Host",
        goal="Create an engaging introduction for the debate",
        backstory="""You are a charismatic TV debate host known for
        setting up compelling discussions. You know how to introduce
        topics in a way that captures audience attention and frames
        the key questions fairly for both sides.""",
        verbose=False,
        allow_delegation=False,
    )

def generate_tv_host_introduction(
    topic: str,
    research: "ClassifiedResearch",
) -> DebateIntroduction:
    """
    Generate TV-style debate introduction.

    Args:
        topic: Debate topic
        research: Classified research for context

    Returns:
        DebateIntroduction with opening and questions
    """
    # Build opening
    opening_parts = [
        f"Good evening and welcome to tonight's debate!",
        f"Our topic: {topic}",
        "",
        "This is a question that affects millions of people and sparks ",
        "passionate disagreement on both sides.",
    ]

    # Add context from research
    if research.statistics:
        stat = research.statistics[0]
        opening_parts.append(f" Consider this: {stat}")

    opening_parts.append("")
    opening_parts.append(
        "Tonight, our debaters will present their strongest arguments. "
        "Let's begin!"
    )

    opening = " ".join(opening_parts)

    # Generate key questions
    key_questions = _generate_key_questions(topic, research)

    return DebateIntroduction(
        opening=opening,
        key_questions=key_questions,
    )

def _generate_key_questions(
    topic: str,
    research: "ClassifiedResearch",
) -> list[str]:
    """Generate key debate questions."""
    questions = []

    # Question from pro perspective
    if research.pro_points:
        questions.append(f"Can the benefits outweigh the costs?")

    # Question from con perspective
    if research.con_points:
        questions.append(f"What are the risks we should consider?")

    # General framing questions
    questions.extend([
        "Who will be most affected by this?",
        "What does the evidence really tell us?",
        "Is there a middle ground?",
    ])

    return questions[:5]
```

### 4.9 Teacher Agent

**File**: `src/crew/agents/teacher_agent.py`

**Purpose**: Generate structured educational lessons.

```python
from dataclasses import dataclass
from crewai import Agent

@dataclass
class Lesson:
    """A structured educational lesson."""
    title: str
    overview: str                       # 2-3 paragraph introduction
    key_concepts: list[str]             # Main ideas (3-5)
    detailed_explanations: dict         # concept → explanation
    examples: list[str]                 # Real-world examples
    quiz_questions: list[str]           # Knowledge check questions
    summary: str                        # Brief recap
    detail_level: str                   # beginner/intermediate/advanced

def create_teacher_agent() -> Agent:
    """Create teacher agent."""
    return Agent(
        role="Expert Teacher",
        goal="Create comprehensive, engaging educational content",
        backstory="""You are an experienced educator with a gift for
        making complex topics accessible. You break down difficult
        concepts into understandable parts and use examples to
        illustrate key points. You adapt your teaching to the
        student's level.""",
        verbose=False,
        allow_delegation=False,
    )
```

---

## 5. ALL 4 CREWAI TOOLS

### 5.1 Debate Generation Tool

**File**: `src/crew/tools/debate_tool.py` (432 lines)

**Purpose**: Generate debate arguments with history awareness and output cleaning.

```python
from dataclasses import dataclass, field
from crewai_tools import BaseTool
from pydantic import Field

@dataclass
class DebateTurn:
    """A single turn in the debate."""
    stance: str         # "pro" or "con"
    argument: str       # The argument text
    round_num: int      # Round number

class DebateGenerationTool(BaseTool):
    """
    Generate debate arguments with full history awareness.

    This tool maintains debate history and generates contextually
    appropriate arguments (opening statements vs rebuttals).
    """

    name: str = "debate_generator"
    description: str = "Generate debate arguments based on topic, stance, and context"

    # Configuration
    model_manager: Any = Field(default=None, exclude=True)
    stance: str = Field(default="pro")

    # Internal state
    _debate_history: list = field(default_factory=list)

    def __init__(
        self,
        model_manager: "DualModelManager",
        stance: str = "pro",
    ):
        super().__init__()
        self.model_manager = model_manager
        self.stance = stance
        self._debate_history = []

    def _run(
        self,
        topic: str,
        stance: str,
        domain: str = "debate",
        research_context: str = "",
        round_num: int = 1,
    ) -> str:
        """
        Generate a debate argument.

        Args:
            topic: Debate topic
            stance: "pro" or "con"
            domain: Domain for adapter selection
            research_context: Supporting research
            round_num: Current round (1 = opening, 2+ = rebuttal)

        Returns:
            Generated argument string
        """
        # Build prompt
        prompt = self._build_prompt(
            topic=topic,
            stance=stance,
            research_context=research_context,
            round_num=round_num,
        )

        # Generate using appropriate model
        if stance == "pro":
            raw_output = self.model_manager.generate_pro(
                prompt=prompt,
                max_tokens=300,
                temperature=0.7,
            )
        else:
            raw_output = self.model_manager.generate_con(
                prompt=prompt,
                max_tokens=300,
                temperature=0.7,
            )

        # Clean output
        cleaned = self._clean_output(raw_output)

        # Limit sentences
        cleaned = self._limit_sentences(cleaned, max_sentences=10)

        # Add to history
        turn = DebateTurn(stance=stance, argument=cleaned, round_num=round_num)
        self._debate_history.append(turn)

        return cleaned

    def _build_prompt(
        self,
        topic: str,
        stance: str,
        research_context: str,
        round_num: int,
    ) -> str:
        """Build the generation prompt."""

        # Determine prompt type
        is_opening = round_num == 1

        if is_opening:
            return self._build_opening_prompt(topic, stance, research_context)
        else:
            return self._build_rebuttal_prompt(topic, stance, research_context, round_num)

    def _build_opening_prompt(
        self,
        topic: str,
        stance: str,
        research_context: str,
    ) -> str:
        """Build opening statement prompt."""
        stance_name = "PRO (arguing IN FAVOR)" if stance == "pro" else "CON (arguing AGAINST)"

        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a passionate, articulate debater in a live public debate. Your goal is to WIN the audience to YOUR side.

CRITICAL STYLE RULES:
- Speak naturally like a confident human advocate, NOT like a robot or ChatGPT
- NEVER start with "I will argue that..." or "In this debate, I will..."
- NEVER use phrases like "As an AI" or "I don't have personal opinions"
- START with a powerful hook: a provocative question, striking fact, or bold claim
- Use rhetorical questions to engage the audience
- Include ONE vivid real-world example or analogy
- Show genuine emotion and conviction in your words
- End with a memorable, quotable closing line

Your side: {stance_name}
Length: 6-10 sentences, no more.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Use these facts to strengthen your argument:
{research_context}

DEBATE TOPIC: {topic}

Write a compelling opening argument for the {stance.upper()} side. Start with a hook, present 2-3 strong points with evidence, and end with a memorable statement.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    def _build_rebuttal_prompt(
        self,
        topic: str,
        stance: str,
        research_context: str,
        round_num: int,
    ) -> str:
        """Build rebuttal prompt with opponent's last argument."""
        stance_name = "PRO" if stance == "pro" else "CON"
        opponent_stance = "con" if stance == "pro" else "pro"

        # Get opponent's last argument
        opponent_arg = ""
        for turn in reversed(self._debate_history):
            if turn.stance == opponent_stance:
                opponent_arg = turn.argument[:400]  # Limit length
                break

        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a passionate debater responding to your opponent in a live debate. Your goal is to DEMOLISH their argument while strengthening your own position.

CRITICAL STYLE RULES:
- START by directly quoting or paraphrasing ONE specific claim they made, then attack it
- Use phrases like "My opponent claims...", "Really?", "Let's examine that claim", "Here's what they're missing"
- Point out logical flaws, missing context, or cherry-picked facts in their argument
- Provide counter-evidence or a better interpretation of the data
- Add ONE new point for your side that they haven't addressed
- Show passion - be firm and confident but not rude
- End with a powerful statement that reframes the debate in your favor

Your side: {stance_name}
This is round {round_num} - you are responding to their argument.
Length: 6-10 sentences, no more.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Your research:
{research_context}

DEBATE TOPIC: {topic}

The other side just argued:
"{opponent_arg}"

Now COUNTER their argument and advance YOUR position ({stance_name}).
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    def _clean_output(self, text: str) -> str:
        """
        Clean LLM output to remove artifacts.

        Removes:
        - Markdown formatting (**bold**, #headers, etc.)
        - Meta-commentary ("Here is a compelling argument...")
        - Instruction artifacts ("Remember to...")
        - Code blocks
        - Numbered lists that look like instructions
        """
        if not text:
            return ""

        # Remove markdown bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        # Remove code blocks
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)

        # Remove meta-commentary lines
        meta_patterns = [
            r'^Here is .*?argument.*?:?\s*',
            r'^Here\'s .*?argument.*?:?\s*',
            r'^I will argue.*?:?\s*',
            r'^In this debate.*?:?\s*',
            r'^As requested.*?:?\s*',
            r'^Sure.*?argument.*?:?\s*',
            r'^Okay.*?argument.*?:?\s*',
            r'^Remember:.*$',
            r'^Note:.*$',
            r'^\[.*?\]$',  # [Instructions in brackets]
        ]
        for pattern in meta_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)

        # Remove numbered instruction lists
        text = re.sub(r'^\d+\.\s+[A-Z][^.]*:\s*', '', text, flags=re.MULTILINE)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'  +', ' ', text)
        text = text.strip()

        return text

    def _limit_sentences(self, text: str, max_sentences: int = 10) -> str:
        """Limit text to maximum number of sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if len(sentences) <= max_sentences:
            return text

        return ' '.join(sentences[:max_sentences])

    def add_external_turn(self, stance: str, argument: str, round_num: int):
        """
        Add opponent's turn to history for awareness.

        Called by DebateCrew to let each debater know what
        the other side argued.
        """
        turn = DebateTurn(stance=stance, argument=argument, round_num=round_num)
        self._debate_history.append(turn)

    def clear_history(self):
        """Clear debate history for new debate."""
        self._debate_history = []

    def get_history(self) -> list[DebateTurn]:
        """Get full debate history."""
        return self._debate_history.copy()
```

### 5.2 Internet Research Tool

**File**: `src/crew/tools/internet_research.py` (150+ lines)

```python
import hashlib
from crewai_tools import BaseTool
from src.utils.web_search import search_duckduckgo

class InternetResearchTool(BaseTool):
    """
    Web search with quality refinement and per-session caching.
    """

    name: str = "internet_research"
    description: str = "Search the internet for debate-relevant information"

    # Per-session cache
    _session_cache: dict = {}

    def __init__(self):
        super().__init__()
        self._session_cache = {}

    def _run(
        self,
        topic: str,
        search_type: str = "debate",
    ) -> str:
        """
        Execute internet research.

        Args:
            topic: Search query
            search_type: "debate", "experts", or "general"

        Returns:
            Search results as formatted text
        """
        # Check cache
        cache_key = self._cache_key(topic, search_type)
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]

        # Execute search based on type
        if search_type == "debate":
            result = self._search_debate_with_refinement(topic)
        elif search_type == "experts":
            result = self._search_experts(topic)
        else:
            result = self._search_general(topic)

        # Cache result
        self._session_cache[cache_key] = result

        return result

    def _search_debate_with_refinement(
        self,
        topic: str,
        max_retries: int = 5,
    ) -> str:
        """
        Search with auto-refinement if quality too low.
        """
        current_query = topic

        for attempt in range(max_retries):
            # Execute search
            results = self._search_debate(current_query)

            if not results:
                continue

            # Evaluate quality
            results_text = self._format_results(results)
            evaluation = evaluate_research_quality(results_text, topic)

            print(f"  [Attempt {attempt+1}/{max_retries}] Score: {evaluation.score}/100")

            if evaluation.is_acceptable:
                return results_text

            # Refine query based on issues
            current_query = self._refine_query(topic, evaluation.issues)

        # Return best effort
        return self._format_results(results) if results else ""

    def _search_debate(self, query: str) -> list[dict]:
        """Execute debate-focused search."""
        queries = [
            f"{query} arguments for and against",
            f"{query} benefits problems",
            f"{query} debate facts statistics",
        ]

        all_results = []
        for q in queries:
            results = search_duckduckgo(q, max_results=3)
            all_results.extend(results)

        return all_results

    def _search_experts(self, query: str) -> str:
        """Search for domain experts."""
        results = search_duckduckgo(f"{query} expert professor researcher", max_results=5)
        return self._format_results(results)

    def _search_general(self, query: str) -> str:
        """General search."""
        results = search_duckduckgo(query, max_results=5)
        return self._format_results(results)

    def _format_results(self, results: list[dict]) -> str:
        """Format search results as text."""
        parts = []
        for r in results:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            url = r.get("url", "")

            if snippet:
                parts.append(f"{title}: {snippet}")

        return "\n\n".join(parts)

    def _refine_query(self, original: str, issues: list[str]) -> str:
        """Refine query based on identified issues."""
        refinements = {
            "relevance": f"{original} specifically explained",
            "specificity": f"{original} statistics data facts",
            "perspective": f"{original} arguments for and against",
            "credibility": f"{original} academic research university",
        }

        for issue in issues:
            if issue in refinements:
                return refinements[issue]

        return f"{original} comprehensive overview"

    def _cache_key(self, topic: str, search_type: str) -> str:
        """Generate cache key."""
        content = f"{topic}:{search_type}"
        return hashlib.md5(content.encode()).hexdigest()

    def clear_cache(self):
        """Clear session cache."""
        self._session_cache = {}
```

### 5.3 Wikipedia Tool

**File**: `src/crew/tools/wikipedia_tool.py` (100+ lines)

```python
import wikipedia
from crewai_tools import BaseTool

class WikipediaSearchTool(BaseTool):
    """
    Access Wikipedia for topic research and expert discovery.
    """

    name: str = "wikipedia_search"
    description: str = "Search Wikipedia for information on any topic"

    # Session cache
    _cache: dict = {}

    def __init__(self):
        super().__init__()
        self._cache = {}

    def _run(
        self,
        query: str,
        search_type: str = "summary",
        sentences: int = 5,
    ) -> str:
        """
        Execute Wikipedia search.

        Args:
            query: Search query
            search_type: "summary", "experts", or "full"
            sentences: Number of sentences for summary

        Returns:
            Wikipedia content
        """
        cache_key = f"{query}:{search_type}:{sentences}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if search_type == "summary":
                result = self._get_summary(query, sentences)
            elif search_type == "experts":
                result = self._search_experts(query)
            elif search_type == "full":
                result = self._get_full_page(query)
            else:
                result = self._get_summary(query, sentences)

            self._cache[cache_key] = result
            return result

        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation by trying first option
            if e.options:
                return self._get_summary(e.options[0], sentences)
            return ""

        except wikipedia.exceptions.PageError:
            return ""

        except Exception as e:
            print(f"Wikipedia error: {e}")
            return ""

    def _get_summary(self, query: str, sentences: int) -> str:
        """Get Wikipedia summary."""
        return wikipedia.summary(query, sentences=sentences)

    def _search_experts(self, query: str) -> str:
        """Search for people/experts."""
        # Search for pages
        results = wikipedia.search(query, results=5)

        expert_info = []
        for title in results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                # Check if it's about a person
                categories = page.categories
                is_person = any(
                    "people" in cat.lower() or
                    "births" in cat.lower() or
                    "deaths" in cat.lower()
                    for cat in categories
                )

                if is_person:
                    summary = wikipedia.summary(title, sentences=2)
                    expert_info.append(f"{title}: {summary}")
            except:
                continue

        return "\n\n".join(expert_info)

    def _get_full_page(self, query: str) -> str:
        """Get full Wikipedia page content."""
        page = wikipedia.page(query)
        # Limit to reasonable length
        return page.content[:5000]

    def clear_cache(self):
        """Clear session cache."""
        self._cache = {}
```

### 5.4 Research Quality Evaluator

**File**: `src/crew/tools/research_evaluator.py` (213 lines)

```python
from dataclasses import dataclass

@dataclass
class ResearchEvaluation:
    """Result of research quality evaluation."""
    score: int                      # 0-100 overall score
    is_acceptable: bool             # Score >= threshold
    issues: list[str]               # Identified quality issues
    breakdown: dict                 # Score per criterion

# Scoring rubric
CRITERIA = {
    "relevance": {
        "max_points": 30,
        "description": "How relevant is the content to the topic",
    },
    "specificity": {
        "max_points": 20,
        "description": "Presence of specific facts, numbers, dates",
    },
    "diversity": {
        "max_points": 10,
        "description": "Multiple perspectives represented",
    },
    "credibility": {
        "max_points": 15,
        "description": "Expert sources, academic references",
    },
    "length": {
        "max_points": 15,
        "description": "Sufficient detail and comprehensiveness",
    },
    "general": {
        "max_points": 10,
        "description": "Overall quality factors",
    },
}

# Issue-specific query refinements
REFINED_QUERIES = {
    "empty": [
        "{topic} definition overview",
        "what is {topic}",
    ],
    "relevance": [
        "{topic} specifically explained",
        "{topic} in detail",
    ],
    "specificity": [
        "{topic} statistics data facts",
        "{topic} numbers figures",
    ],
    "perspective": [
        "{topic} arguments for and against",
        "{topic} pros cons debate",
    ],
    "credibility": [
        "{topic} academic research university",
        "{topic} expert analysis study",
    ],
}

def evaluate_research_quality(
    research_text: str,
    topic: str,
    threshold: int = 60,
) -> ResearchEvaluation:
    """
    Evaluate the quality of research text.

    Args:
        research_text: The research content to evaluate
        topic: Original topic for relevance checking
        threshold: Minimum acceptable score (default 60)

    Returns:
        ResearchEvaluation with detailed scoring
    """
    if not research_text or len(research_text.strip()) < 50:
        return ResearchEvaluation(
            score=0,
            is_acceptable=False,
            issues=["empty"],
            breakdown={},
        )

    breakdown = {}
    issues = []

    # 1. RELEVANCE (0-30 points)
    relevance = _score_relevance(research_text, topic)
    breakdown["relevance"] = relevance
    if relevance < 15:
        issues.append("relevance")

    # 2. SPECIFICITY (0-20 points)
    specificity = _score_specificity(research_text)
    breakdown["specificity"] = specificity
    if specificity < 10:
        issues.append("specificity")

    # 3. DIVERSITY (0-10 points)
    diversity = _score_diversity(research_text)
    breakdown["diversity"] = diversity
    if diversity < 5:
        issues.append("perspective")

    # 4. CREDIBILITY (0-15 points)
    credibility = _score_credibility(research_text)
    breakdown["credibility"] = credibility
    if credibility < 7:
        issues.append("credibility")

    # 5. LENGTH (0-15 points)
    length = _score_length(research_text)
    breakdown["length"] = length

    # 6. GENERAL (0-10 points)
    general = _score_general(research_text)
    breakdown["general"] = general

    # Total score
    total = sum(breakdown.values())

    return ResearchEvaluation(
        score=total,
        is_acceptable=total >= threshold,
        issues=issues,
        breakdown=breakdown,
    )

def _score_relevance(text: str, topic: str) -> int:
    """Score topic relevance (0-30)."""
    text_lower = text.lower()

    # Extract topic keywords
    topic_words = set(topic.lower().split())
    topic_words -= {"should", "be", "the", "a", "an", "is", "are", "of", "to"}

    if not topic_words:
        return 15  # Default if no keywords

    # Count keyword occurrences
    matches = sum(1 for word in topic_words if word in text_lower)
    match_ratio = matches / len(topic_words)

    return int(min(30, match_ratio * 40))

def _score_specificity(text: str) -> int:
    """Score specificity (0-20)."""
    score = 0

    # Numbers
    numbers = re.findall(r'\d+', text)
    score += min(8, len(numbers) * 2)

    # Percentages
    percentages = re.findall(r'\d+\s*%', text)
    score += min(4, len(percentages) * 2)

    # Dates/years
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    score += min(4, len(years))

    # Quotes
    quotes = re.findall(r'"[^"]{10,}"', text)
    score += min(4, len(quotes) * 2)

    return min(20, score)

def _score_diversity(text: str) -> int:
    """Score perspective diversity (0-10)."""
    text_lower = text.lower()

    pro_indicators = ["benefit", "advantage", "positive", "support", "favor"]
    con_indicators = ["problem", "risk", "concern", "against", "negative"]

    has_pro = any(ind in text_lower for ind in pro_indicators)
    has_con = any(ind in text_lower for ind in con_indicators)

    if has_pro and has_con:
        return 10
    elif has_pro or has_con:
        return 5
    return 2

def _score_credibility(text: str) -> int:
    """Score source credibility (0-15)."""
    text_lower = text.lower()
    score = 0

    credibility_markers = [
        "according to", "research", "study", "professor", "university",
        "expert", "scientist", "data", "evidence", "report",
    ]

    for marker in credibility_markers:
        if marker in text_lower:
            score += 2

    return min(15, score)

def _score_length(text: str) -> int:
    """Score content length (0-15)."""
    word_count = len(text.split())

    if word_count < 50:
        return 2
    elif word_count < 100:
        return 5
    elif word_count < 200:
        return 8
    elif word_count < 400:
        return 12
    else:
        return 15

def _score_general(text: str) -> int:
    """Score general quality (0-10)."""
    score = 5  # Base score

    # Coherent sentences (not just keywords)
    sentences = re.split(r'[.!?]+', text)
    valid_sentences = [s for s in sentences if len(s.split()) >= 5]

    if len(valid_sentences) >= 5:
        score += 3
    elif len(valid_sentences) >= 3:
        score += 2

    # No error messages or empty results
    error_indicators = ["not found", "no results", "error", "unavailable"]
    if not any(ind in text.lower() for ind in error_indicators):
        score += 2

    return min(10, score)
```

---

## 6. PROMPT ENGINEERING TECHNIQUES

### 6.1 Llama Chat Template Format

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

[System prompt with role and constraints]
<|eot_id|><|start_header_id|>user<|end_header_id|>

[User message with context and instructions]
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

[Model generates response here]
```

### 6.2 Key Prompt Engineering Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Role Persona** | Strong character definition | "You are a passionate debater..." |
| **Explicit Constraints** | Length and format rules | "5-10 sentences, no more" |
| **Negative Examples** | What NOT to do | "NEVER start with 'I will argue...'" |
| **Hook Requirement** | Force engaging openings | "START with a powerful hook" |
| **Evidence Integration** | Use provided research | "Use these facts to strengthen..." |
| **Rebuttal Framing** | Quote and attack | "directly quoting ONE specific claim" |
| **Emotional Tone** | Human-like passion | "Show genuine emotion and conviction" |

### 6.3 Opening Statement Prompt (Full)

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a passionate, articulate debater in a live public debate. Your goal is to WIN the audience to YOUR side.

CRITICAL STYLE RULES:
- Speak naturally like a confident human advocate, NOT like a robot or ChatGPT
- NEVER start with "I will argue that..." or "In this debate, I will..."
- NEVER use phrases like "As an AI" or "I don't have personal opinions"
- START with a powerful hook: a provocative question, striking fact, or bold claim
- Use rhetorical questions to engage the audience
- Include ONE vivid real-world example or analogy
- Show genuine emotion and conviction in your words
- End with a memorable, quotable closing line

Your side: PRO (arguing IN FAVOR of the topic)
Length: 6-10 sentences, no more.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Use these facts to strengthen your argument:
[RESEARCH_CONTEXT]

DEBATE TOPIC: [TOPIC]

Write a compelling opening argument for the PRO side. Start with a hook, present 2-3 strong points with evidence, and end with a memorable statement.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

### 6.4 Rebuttal Prompt (Full)

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a passionate debater responding to your opponent in a live debate. Your goal is to DEMOLISH their argument while strengthening your own position.

CRITICAL STYLE RULES:
- START by directly quoting or paraphrasing ONE specific claim they made, then attack it
- Use phrases like "My opponent claims...", "Really?", "Let's examine that claim", "Here's what they're missing"
- Point out logical flaws, missing context, or cherry-picked facts in their argument
- Provide counter-evidence or a better interpretation of the data
- Add ONE new point for your side that they haven't addressed
- Show passion - be firm and confident but not rude
- End with a powerful statement that reframes the debate in your favor

Your side: CON (arguing AGAINST)
This is round 2 - you are responding to their argument.
Length: 6-10 sentences, no more.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Your research:
[RESEARCH_CONTEXT]

DEBATE TOPIC: [TOPIC]

The other side just argued:
"[OPPONENT_ARGUMENT]"

Now COUNTER their argument and advance YOUR position (CON).
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

---

## 7. OUTPUT CLEANING ALGORITHMS

### 7.1 Markdown Removal

```python
# Bold/italic
text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** → bold
text = re.sub(r'\*([^*]+)\*', r'\1', text)       # *italic* → italic
text = re.sub(r'__([^_]+)__', r'\1', text)       # __bold__ → bold
text = re.sub(r'_([^_]+)_', r'\1', text)         # _italic_ → italic

# Headers
text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # # Header → Header

# Code blocks
text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
text = re.sub(r'`[^`]+`', '', text)
```

### 7.2 Meta-Commentary Removal

```python
meta_patterns = [
    r'^Here is .*?argument.*?:?\s*',      # "Here is a compelling argument:"
    r'^Here\'s .*?argument.*?:?\s*',      # "Here's my argument:"
    r'^I will argue.*?:?\s*',             # "I will argue that..."
    r'^In this debate.*?:?\s*',           # "In this debate, I will..."
    r'^As requested.*?:?\s*',             # "As requested, here is..."
    r'^Sure.*?argument.*?:?\s*',          # "Sure, here's an argument:"
    r'^Okay.*?argument.*?:?\s*',          # "Okay, here's my argument:"
    r'^Remember:.*$',                     # "Remember: stay on topic"
    r'^Note:.*$',                         # "Note: this is important"
    r'^\[.*?\]$',                         # "[Instructions in brackets]"
]

for pattern in meta_patterns:
    text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
```

### 7.3 Instruction List Removal

```python
# Remove numbered instruction lists
# Matches: "1. Start with: ...", "2. Include: ..."
text = re.sub(r'^\d+\.\s+[A-Z][^.]*:\s*', '', text, flags=re.MULTILINE)
```

### 7.4 Whitespace Cleanup

```python
# Multiple newlines → double newline
text = re.sub(r'\n{3,}', '\n\n', text)

# Multiple spaces → single space
text = re.sub(r'  +', ' ', text)

# Trim
text = text.strip()
```

### 7.5 Sentence Limiting

```python
def _limit_sentences(text: str, max_sentences: int = 10) -> str:
    """Limit text to maximum number of sentences."""
    # Split on sentence endings followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)

    if len(sentences) <= max_sentences:
        return text

    # Join only first N sentences
    return ' '.join(sentences[:max_sentences])
```

---

## 8. QUALITY REFINEMENT SYSTEM

### 8.1 Refinement Loop

```python
def _search_debate_with_refinement(self, topic: str, max_retries: int = 5) -> str:
    """
    Search with automatic query refinement if quality is too low.

    Flow:
    1. Execute initial search
    2. Evaluate result quality (0-100)
    3. If score < 60: refine query and retry
    4. Repeat until acceptable or max retries
    """
    current_query = topic

    for attempt in range(max_retries):
        # Execute search
        results = self._search_debate(current_query)

        if not results:
            continue

        # Format and evaluate
        results_text = self._format_results(results)
        evaluation = evaluate_research_quality(results_text, topic)

        print(f"  [Attempt {attempt+1}/{max_retries}] Score: {evaluation.score}/100")

        # Check if acceptable
        if evaluation.is_acceptable:
            return results_text

        # Refine query based on identified issues
        current_query = self._refine_query(topic, evaluation.issues)

    # Return best effort after all retries
    return self._format_results(results) if results else ""
```

### 8.2 Issue-Based Query Refinement

```python
REFINED_QUERIES = {
    "empty": [
        "{topic} definition overview",
        "what is {topic}",
    ],
    "relevance": [
        "{topic} specifically explained",
        "{topic} in detail",
    ],
    "specificity": [
        "{topic} statistics data facts",
        "{topic} numbers figures",
    ],
    "perspective": [
        "{topic} arguments for and against",
        "{topic} pros cons debate",
    ],
    "credibility": [
        "{topic} academic research university",
        "{topic} expert analysis study",
    ],
}

def _refine_query(self, original: str, issues: list[str]) -> str:
    """
    Generate refined query based on quality issues.

    Args:
        original: Original search query
        issues: List of identified quality issues

    Returns:
        Refined query string
    """
    for issue in issues:
        if issue in REFINED_QUERIES:
            template = REFINED_QUERIES[issue][0]
            return template.format(topic=original)

    # Default refinement
    return f"{original} comprehensive overview"
```

### 8.3 Scoring Breakdown

| Criterion | Max Points | What It Measures |
|-----------|------------|------------------|
| **Relevance** | 30 | Topic keyword presence |
| **Specificity** | 20 | Numbers, dates, quotes |
| **Diversity** | 10 | Pro AND con perspectives |
| **Credibility** | 15 | Expert/academic indicators |
| **Length** | 15 | Word count adequacy |
| **General** | 10 | Coherent sentences, no errors |

**Threshold**: Score must be ≥ 60 to be considered acceptable.

---

## 9. CACHING STRATEGY

### 9.1 Per-Session Caching

Each debate session has its own cache that is cleared at the start of a new debate:

```python
class DebateCrew:
    def _clear_session_caches(self):
        """Clear all per-session caches for fresh debate."""
        if self._wikipedia_tool:
            self._wikipedia_tool.clear_cache()
        if self._internet_tool:
            self._internet_tool.clear_cache()
        if self._pro_debate_tool:
            self._pro_debate_tool.clear_history()
        if self._con_debate_tool:
            self._con_debate_tool.clear_history()
```

### 9.2 MD5 Cache Keys

```python
def _cache_key(self, topic: str, search_type: str) -> str:
    """Generate deterministic cache key."""
    content = f"{topic}:{search_type}"
    return hashlib.md5(content.encode()).hexdigest()
```

### 9.3 Cache Benefits

| Benefit | Description |
|---------|-------------|
| **Deduplication** | Same query returns cached result |
| **Speed** | No redundant API calls |
| **Consistency** | Same topic gets same research within session |
| **Isolation** | New debate gets fresh data |

---

## 10. ERROR HANDLING

### 10.1 Wikipedia Errors

```python
try:
    result = wikipedia.summary(query, sentences=sentences)
except wikipedia.exceptions.DisambiguationError as e:
    # Handle ambiguous terms by trying first option
    if e.options:
        result = wikipedia.summary(e.options[0], sentences)
except wikipedia.exceptions.PageError:
    # Page doesn't exist
    result = ""
except Exception as e:
    print(f"Wikipedia error: {e}")
    result = ""
```

### 10.2 Model Generation Errors

```python
try:
    with torch.no_grad():
        outputs = model.generate(**inputs, ...)
except RuntimeError as e:
    if "out of memory" in str(e):
        # CUDA OOM - clear cache and retry with smaller batch
        torch.cuda.empty_cache()
        # Retry with reduced max_tokens
    raise
```

### 10.3 Adapter Loading Errors

```python
try:
    model = PeftModel.from_pretrained(model, adapter_path, is_trainable=False)
except Exception as e:
    print(f"Failed to load adapter: {e}")
    # Continue with base model (no adapter)
    return False
```

### 10.4 Graceful Degradation

The system is designed to degrade gracefully:

1. **No internet** → Uses Wikipedia only
2. **No adapter found** → Uses base model
3. **Low quality research** → Proceeds with available data
4. **Wikipedia disambiguation** → Tries first option
5. **Search fails** → Returns empty string, continues debate

---

## SUMMARY

The CrewAI system provides:

- **11 Specialized Agents**: Each with a clear role in the debate pipeline
- **4 Powerful Tools**: Debate generation, Wikipedia, internet search, quality evaluation
- **Dual Model Architecture**: True independence between Pro and Con
- **Dynamic Adapter Loading**: Domain specialization without model reload
- **Quality Refinement**: Automatic improvement of research quality
- **Aggressive Output Cleaning**: Natural, human-like debate arguments
- **Per-Session Caching**: Fast performance with fresh data per debate
- **Graceful Error Handling**: Robust operation despite failures

This architecture enables realistic, well-researched AI debates on any topic.

---

*Continue to [DETAILED_PROJECT_EXPLICATION_BACKEND.md](./DETAILED_PROJECT_EXPLICATION_BACKEND.md) for Python backend details.*
