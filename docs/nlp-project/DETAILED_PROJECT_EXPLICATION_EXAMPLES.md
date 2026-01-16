# DATA FLOW & COMPLETE EXAMPLES

> **Complete Technical Documentation with Real-World Examples**
>
> This document provides end-to-end examples showing how data flows through the entire system.

---

## TABLE OF CONTENTS

1. [Complete Debate Example](#1-complete-debate-example)
2. [Training Pipeline Example](#2-training-pipeline-example)
3. [API Request/Response Examples](#3-api-requestresponse-examples)
4. [Output Artifacts](#4-output-artifacts)
5. [Troubleshooting Guide](#5-troubleshooting-guide)
6. [Performance Benchmarks](#6-performance-benchmarks)
7. [Configuration Reference](#7-configuration-reference)

---

## 1. COMPLETE DEBATE EXAMPLE

### 1.1 Input

```bash
python scripts/run_debate_crew.py "Should electric vehicles be mandatory by 2035?" --rounds 2 --use-internet --recommend-guests
```

### 1.2 Step-by-Step Execution

#### Step 1: Topic Analysis

**Input**: `"Should electric vehicles be mandatory by 2035?"`

**Processing**:
```python
# No grammar corrections needed
corrected_topic = "Should electric vehicles be mandatory by 2035?"

# Key terms extracted
key_terms = ["electric", "vehicles", "mandatory", "2035"]

# Domain detected via keyword matching
domain_scores = {
    "technology": 3,  # "electric", "vehicles"
    "environment": 1, # implicitly related
    "economics": 1,   # policy implication
}
domain_hint = "technology"

# Research queries generated
research_queries = [
    "Should electric vehicles be mandatory by 2035 debate 2026",
    "electric vehicles benefits advantages",
    "electric vehicles problems concerns risks",
    "electric vehicles statistics data facts 2026",
    "electric vehicles expert opinion analysis",
    "electric vehicles arguments for against",
]

# Persona queries generated
persona_queries = [
    "technology expert electric vehicles",
    "electric vehicles researcher professor",
    "electric vehicles policy analyst",
]
```

**Output**: `TopicAnalysis` object

---

#### Step 2: Research Gathering

**Wikipedia Search Results**:
```
[Wikipedia] Electric vehicle: An electric vehicle (EV) is a vehicle that uses
one or more electric motors for propulsion. EVs include road vehicles such as
electric cars, trucks, buses, and two-wheelers, as well as boats, aircraft,
and spacecraft. The global electric car fleet has been growing rapidly, with
sales increasing by 35% in 2025 compared to the previous year.

[Wikipedia] Electric car: An electric car is an automobile propelled by one or
more electric motors, using only energy stored in batteries. Compared to
internal combustion engine vehicles, electric cars are quieter, have no
tailpipe emissions, and lower emissions overall. The first practical electric
cars were produced in the 1880s.
```

**Internet Search Results** (DuckDuckGo):
```
[Web] IEA Report 2025: Global EV sales reached 18 million units in 2025,
representing 22% of all new car sales. China leads with 60% of global EV
sales, followed by Europe (25%) and the United States (10%).

[Web] Critics argue that EV mandates could disproportionately affect
lower-income households who cannot afford the higher upfront costs.
Additionally, rural areas may lack adequate charging infrastructure.

[Web] A study by BloombergNEF suggests that EVs will reach price parity
with internal combustion vehicles by 2027, making mandates potentially
unnecessary as market forces take over.

[Web] The mining of lithium, cobalt, and rare earth elements for EV
batteries raises environmental and ethical concerns about the supply chain.
```

**Quality Evaluation**:
```python
evaluation = ResearchEvaluation(
    score=82,
    is_acceptable=True,
    issues=[],
    breakdown={
        "relevance": 28,      # High topic keyword presence
        "specificity": 18,    # Good statistics (35%, 18 million, 22%)
        "diversity": 10,      # Both pro and con perspectives
        "credibility": 12,    # IEA, BloombergNEF citations
        "length": 14,         # Adequate detail
    }
)
```

**Combined Research Context** (truncated):
```
Electric vehicle (EV) is a vehicle that uses one or more electric motors...
Global EV sales reached 18 million units in 2025, representing 22%...
Critics argue that EV mandates could disproportionately affect lower-income...
EVs will reach price parity with internal combustion vehicles by 2027...
Mining of lithium, cobalt, and rare earth elements raises concerns...
```

---

#### Step 3: Research Classification

**Input**: Combined research context

**Output**: `ClassifiedResearch` object
```python
ClassifiedResearch(
    topic="Should electric vehicles be mandatory by 2035?",

    pro_points=[
        "Global EV sales increased by 35% in 2025, showing strong market momentum",
        "EVs have no tailpipe emissions and lower overall emissions",
        "EVs are quieter and have lower long-term operating costs",
        "Price parity with ICE vehicles expected by 2027",
    ],

    con_points=[
        "EV mandates could disproportionately affect lower-income households",
        "Rural areas lack adequate charging infrastructure",
        "Battery production raises environmental and ethical supply chain concerns",
        "Higher upfront costs remain a barrier for many consumers",
    ],

    key_facts=[
        "Global electric car fleet has been growing rapidly",
        "China leads with 60% of global EV sales",
        "First practical electric cars were produced in the 1880s",
    ],

    statistics=[
        "35% increase in EV sales in 2025",
        "18 million EV units sold globally in 2025",
        "22% of all new car sales are EVs",
        "60% of global EV sales in China",
        "Price parity expected by 2027",
    ],

    sources=["IEA", "BloombergNEF", "Wikipedia"],
    quality_score=78,
)
```

---

#### Step 4: Format Research for Debaters

**Pro Context**:
```
SUPPORTING EVIDENCE:
• Global EV sales increased by 35% in 2025, showing strong market momentum
• EVs have no tailpipe emissions and lower overall emissions
• EVs are quieter and have lower long-term operating costs
• Price parity with ICE vehicles expected by 2027

COUNTER-ARGUMENTS TO ADDRESS:
• EV mandates could disproportionately affect lower-income households
• Rural areas lack adequate charging infrastructure

KEY STATISTICS:
• 35% increase in EV sales in 2025
• 18 million EV units sold globally
• 22% of all new car sales are EVs
```

**Con Context**:
```
SUPPORTING EVIDENCE:
• EV mandates could disproportionately affect lower-income households
• Rural areas lack adequate charging infrastructure
• Battery production raises environmental and ethical supply chain concerns
• Higher upfront costs remain a barrier for many consumers

COUNTER-ARGUMENTS TO ADDRESS:
• Global EV sales increased by 35% in 2025
• Price parity with ICE vehicles expected by 2027

KEY STATISTICS:
• 60% of global EV sales concentrated in China
• Price parity not until 2027
```

---

#### Step 5: TV Host Introduction

**Output**:
```
Good evening and welcome to tonight's debate! Our topic: Should electric
vehicles be mandatory by 2035?

This is a question that affects millions of drivers, automakers, and the
future of our planet. With EV sales growing 35% in 2025 and climate
pressure mounting, the stakes couldn't be higher.

Tonight's key questions:
• Can the power grid handle universal EV adoption?
• What about rural communities without charging infrastructure?
• Is the environmental benefit real when considering battery production?
• Should governments mandate or let markets decide?
• Who wins and who loses under EV mandates?

Let's begin!
```

---

#### Step 6: Debate Round 1

**Pro Opening Argument**:

*Prompt sent to Pro model:*
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a passionate, articulate debater in a live public debate...
Your side: PRO (arguing IN FAVOR of the topic)
Length: 6-10 sentences, no more.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Use these facts to strengthen your argument:
SUPPORTING EVIDENCE:
• Global EV sales increased by 35% in 2025...
[full pro context]

DEBATE TOPIC: Should electric vehicles be mandatory by 2035?

Write a compelling opening argument for the PRO side...
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

*Generated output (after cleaning)*:
```
Here's a question for everyone in this room: how many of you have breathed
smog-filled air this year? The answer is all of us, and that's exactly why
we need EV mandates by 2035. The numbers speak for themselves—EV sales
jumped 35% last year alone, proving that people WANT this change. They just
need the push. And let's talk about the elephant in the room: climate change
isn't waiting for market forces. We have twelve years. Twelve. EVs produce
zero tailpipe emissions and are already approaching price parity with gas
guzzlers. Yes, infrastructure needs work—but that's exactly what mandates
drive: investment, innovation, jobs. The auto industry transformed before,
and it will transform again. The only question is whether we lead that
transformation or get left behind. I say we lead.
```

**Con Opening Argument**:

*Generated output (after cleaning)*:
```
My opponent paints a rosy picture, but let me bring us back to reality. Who
pays for this green dream? Not the wealthy—they can afford any car they want.
It's working families, rural communities, and small business owners who'll
bear the burden. You heard the statistic: 60% of EV sales are in China. Why?
Because they have the infrastructure and subsidies we don't. Here in America,
try finding a charging station in rural Montana or West Virginia. Now imagine
telling a farmer their truck is illegal. The inconvenient truth about EVs?
Their batteries require lithium, cobalt, and rare earth minerals mined under
questionable conditions. We're trading one environmental problem for another.
Market forces are already driving EV adoption—35% growth without mandates!
Why rush a mandate that punishes the poor and rewards the privileged?
```

---

#### Step 7: Debate Round 2 (Rebuttals)

**Pro Rebuttal**:

*Prompt includes Con's previous argument*:
```
The other side just argued:
"My opponent paints a rosy picture, but let me bring us back to reality..."
```

*Generated output*:
```
My opponent asks "who pays?" Let me answer directly: we ALL pay if we don't
act. The cost of climate inaction—floods, droughts, wildfires—dwarfs any EV
transition costs. But here's what they conveniently ignored: price parity is
coming in 2027, just two years away. After that, EVs will be CHEAPER than
gas cars. The "burden on working families" argument dissolves when EVs cost
less to buy AND operate. As for rural infrastructure—that's precisely why we
need mandates! Mandates create certainty, certainty attracts investment,
investment builds charging networks. It happened with electricity, with
telephones, with internet. And the battery supply chain? We're already
developing sodium-ion and solid-state alternatives that don't need cobalt.
Innovation follows demand. Give the market a clear signal, and it delivers.
```

**Con Rebuttal**:

*Generated output*:
```
Let's examine that "price parity by 2027" claim. That's a Bloomberg
projection, not a guarantee. Two years ago, they said it would be 2025.
Projections change, but mandates don't. Once you criminalize gas cars, there's
no going back if those projections are wrong. And speaking of infrastructure
investment—who's paying for it? Taxpayers. We're talking about a trillion
dollars to build out charging networks. That's money not going to schools,
hospitals, or housing. My opponent talks about "certainty attracting
investment." You know what else creates certainty? Prison. Mandates aren't
inspiration—they're coercion. The 35% growth they keep citing proves my
point: the market IS working. Consumers ARE choosing EVs. Why do we need
government forcing the issue when freedom is already delivering results?
```

---

#### Step 8: Fact-Checking

**Pro Arguments Analysis**:
```python
fact_check_pro = {
    "num_claims": 12,
    "supported_claims": 9,
    "avg_support_score": 0.68,
    "faithfulness_score": 0.75,
    "verdict": "well_supported",

    "claim_analysis": [
        {"claim": "EV sales jumped 35% last year", "support": 0.95, "supported": True},
        {"claim": "Price parity coming in 2027", "support": 0.85, "supported": True},
        {"claim": "EVs produce zero tailpipe emissions", "support": 0.90, "supported": True},
        {"claim": "Climate change gives us 12 years", "support": 0.40, "supported": True},
        {"claim": "Sodium-ion alternatives being developed", "support": 0.55, "supported": True},
        # ... other claims
    ],
}
```

**Con Arguments Analysis**:
```python
fact_check_con = {
    "num_claims": 11,
    "supported_claims": 7,
    "avg_support_score": 0.58,
    "faithfulness_score": 0.64,
    "verdict": "partially_supported",

    "claim_analysis": [
        {"claim": "60% of EV sales in China", "support": 0.92, "supported": True},
        {"claim": "Trillion dollars for infrastructure", "support": 0.35, "supported": False},
        {"claim": "Battery minerals mined under questionable conditions", "support": 0.70, "supported": True},
        {"claim": "Bloomberg projections have been wrong", "support": 0.45, "supported": True},
        # ... other claims
    ],
}
```

---

#### Step 9: Judging

**Scoring Breakdown**:

| Metric | Pro Round 1 | Pro Round 2 | Con Round 1 | Con Round 2 |
|--------|-------------|-------------|-------------|-------------|
| Length (0-25) | 22 | 21 | 23 | 22 |
| Logic (0-25) | 20 | 18 | 15 | 20 |
| Evidence (0-25) | 20 | 18 | 15 | 12 |
| Civility (0-25) | 25 | 25 | 25 | 23 |
| **Total** | **87** | **82** | **78** | **77** |

**Average Scores**:
- Pro Average: 84.5
- Con Average: 77.5

**With Fact-Check Weighting (70% argument + 30% faithfulness)**:
- Pro Final: 84.5 × 0.7 + 75 × 0.3 = 59.15 + 22.5 = **81.65**
- Con Final: 77.5 × 0.7 + 64 × 0.3 = 54.25 + 19.2 = **73.45**

**Final Judgment**:
```python
JudgeScore(
    pro_score=82,
    con_score=73,
    winner="pro",
    reasoning="""Pro wins with a score of 82 to 73. Pro's arguments were
    better supported by evidence, particularly the statistics on EV growth
    and price parity projections. While Con raised valid concerns about
    infrastructure and equity, several claims lacked specific data support.
    Pro demonstrated stronger use of logical connectors and maintained a
    more consistent evidence-based approach throughout the debate."""
)
```

---

#### Step 10: Guest Recommendations

**Search Process**:
```
Query 1: "technology expert electric vehicles"
→ Wikipedia: Mary Nichols, Sandy Munro

Query 2: "electric vehicles researcher professor"
→ Wikipedia: Daniel Sperling, Jessika Trancik

Query 3: "electric vehicles policy analyst"
→ Web: Michael Liebreich, Colin McKerracher
```

**Validation Results**:
```python
recommended_guests = [
    DebateGuest(
        name="Mary Nichols",
        title="Former Chair, California Air Resources Board",
        expertise="Environmental regulation and EV policy",
        relevance="Key architect of California's zero-emission vehicle mandate",
    ),
    DebateGuest(
        name="Sandy Munro",
        title="Automotive Engineer and Manufacturing Analyst",
        expertise="EV manufacturing, teardown analysis, cost optimization",
        relevance="Provides detailed comparisons of EV vs ICE manufacturing",
    ),
    DebateGuest(
        name="Daniel Sperling",
        title="Professor, UC Davis; Founding Director, ITS-Davis",
        expertise="Transportation technology and policy",
        relevance="Leading academic researcher on sustainable transportation",
    ),
    DebateGuest(
        name="Michael Liebreich",
        title="Founder, BloombergNEF",
        expertise="Clean energy finance and market analysis",
        relevance="Created the data source most cited in EV market projections",
    ),
]
```

---

### 1.3 Final Output

**Console Output**:
```
================================================================================
                              DEBATE RESULTS
================================================================================

Topic: Should electric vehicles be mandatory by 2035?
Domain: technology
Rounds: 2
Duration: 52.3 seconds

--------------------------------------------------------------------------------
                            HOST INTRODUCTION
--------------------------------------------------------------------------------

Good evening and welcome to tonight's debate! Our topic: Should electric
vehicles be mandatory by 2035?
...

--------------------------------------------------------------------------------
                               ROUND 1
--------------------------------------------------------------------------------

PRO:
Here's a question for everyone in this room: how many of you have breathed
smog-filled air this year?...

CON:
My opponent paints a rosy picture, but let me bring us back to reality...

--------------------------------------------------------------------------------
                               ROUND 2
--------------------------------------------------------------------------------

PRO:
My opponent asks "who pays?" Let me answer directly...

CON:
Let's examine that "price parity by 2027" claim...

--------------------------------------------------------------------------------
                             FACT-CHECK
--------------------------------------------------------------------------------

PRO Faithfulness: 0.75 (well_supported)
  - 9/12 claims supported by research

CON Faithfulness: 0.64 (partially_supported)
  - 7/11 claims supported by research

--------------------------------------------------------------------------------
                            FINAL SCORE
--------------------------------------------------------------------------------

PRO: 82 points
CON: 73 points

🏆 WINNER: PRO

Reasoning: Pro wins with a score of 82 to 73. Pro's arguments were better
supported by evidence...

--------------------------------------------------------------------------------
                        RECOMMENDED GUESTS
--------------------------------------------------------------------------------

1. Mary Nichols
   Former Chair, California Air Resources Board
   Expertise: Environmental regulation and EV policy

2. Sandy Munro
   Automotive Engineer and Manufacturing Analyst
   Expertise: EV manufacturing, teardown analysis

3. Daniel Sperling
   Professor, UC Davis
   Expertise: Transportation technology and policy

4. Michael Liebreich
   Founder, BloombergNEF
   Expertise: Clean energy finance and market analysis

================================================================================
Results saved to: runs/debates/20260111_143022_should_electric_vehicles/
================================================================================
```

---

## 2. TRAINING PIPELINE EXAMPLE

### 2.1 Dataset Generation

**Input Command**:
```bash
python scripts/generate_education_dataset.py --domain education --samples 1000
```

**Generated JSONL** (`data/splits/education/train.jsonl`):
```json
{"domain": "education", "topic": "Should homework be abolished in primary schools?", "stance": "pro", "context": "Studies show excessive homework causes stress in young children. Finland, which has minimal homework, consistently ranks high in education. Play-based learning is crucial for child development.", "output": "The evidence is overwhelming: homework harms our youngest learners. Finnish schools assign almost no homework yet produce some of the world's best-educated students. Why? Because children learn through play, exploration, and rest—not worksheets. Research shows that homework before age 10 provides no academic benefit while increasing anxiety and family stress. Let children be children."}
{"domain": "education", "topic": "Should homework be abolished in primary schools?", "stance": "con", "context": "Homework reinforces classroom learning. It teaches responsibility and time management. Parents can engage with their child's education through homework review.", "output": "Abolishing homework throws away a crucial learning tool. When a child practices math at home, they reinforce neural pathways formed in class. More importantly, homework teaches life skills: responsibility, time management, self-discipline. It also gives parents a window into their child's education. The solution isn't abolition—it's thoughtful, age-appropriate assignments that enhance rather than overwhelm."}
```

### 2.2 Training Execution

**Input Command**:
```bash
python scripts/train_education_adapter.py --epochs 3 --batch-size 4
```

**Training Log**:
```
Loading base model from: models/base/llama3.1-nemotron-nano-8b-v1
Model loaded. Device: cuda:0

Preparing model for training...
trainable params: 3,407,872 || all params: 8,030,261,248 || trainable%: 0.0424

Loading dataset from: data/splits/education/
  Train: 800 examples
  Val: 100 examples
  Test: 100 examples

Starting training...
Epoch 1/3
  Step 10/200 | Loss: 2.453 | LR: 1.2e-05
  Step 20/200 | Loss: 2.187 | LR: 2.4e-05
  Step 50/200 | Loss: 1.876 | LR: 5.0e-05
  Eval Loss: 1.923 | Perplexity: 6.84
  Step 100/200 | Loss: 1.654 | LR: 1.0e-04
  Eval Loss: 1.745 | Perplexity: 5.73

Epoch 2/3
  Step 110/200 | Loss: 1.543 | LR: 1.8e-04
  Step 150/200 | Loss: 1.421 | LR: 1.9e-04
  Eval Loss: 1.512 | Perplexity: 4.54
  Step 200/200 | Loss: 1.378 | LR: 2.0e-04
  Eval Loss: 1.456 | Perplexity: 4.29

Epoch 3/3
  Step 250/300 | Loss: 1.298 | LR: 1.5e-04
  Step 300/300 | Loss: 1.245 | LR: 5.0e-05
  Eval Loss: 1.389 | Perplexity: 4.01

Training complete!
Best eval loss: 1.389 at step 300

Saving adapter to: models/adapters/education/
  adapter_config.json (1.2 KB)
  adapter_model.safetensors (3.4 MB)

Total training time: 18 minutes 32 seconds
```

### 2.3 Evaluation Results

**Input Command**:
```bash
python scripts/evaluate_education_adapter.py
```

**Output**:
```
================================================================================
                         ADAPTER EVALUATION RESULTS
================================================================================

Domain: education
Test Set: 100 examples

PERPLEXITY COMPARISON
---------------------
Base Model Perplexity:    8.45
Adapter Perplexity:       4.01
Improvement:              52.5%

GENERATION QUALITY (sample)
---------------------------
Topic: "Should standardized testing be eliminated?"
Stance: PRO

Base Model Output:
"Standardized testing should be eliminated because it is not a good measure
of student learning. Testing causes stress. Students are more than a number.
Education should focus on learning, not testing."

Adapter Output:
"Consider this: we're reducing the full spectrum of human potential to a
single bubble sheet. Standardized tests measure one thing well—the ability
to take standardized tests. They miss creativity, critical thinking,
collaboration, and emotional intelligence. Finland eliminated most
standardized testing and became an education leader. Meanwhile, our
test-obsessed system produces anxious students who can fill bubbles but
can't solve novel problems. It's time to measure what matters."

QUALITY METRICS
---------------
                    Base        Adapter     Improvement
Coherence:          6.2/10      8.4/10      +35%
Relevance:          7.1/10      9.1/10      +28%
Persuasiveness:     5.8/10      8.7/10      +50%
Specificity:        5.5/10      8.2/10      +49%

================================================================================
Adapter significantly outperforms base model on education topics.
================================================================================
```

---

## 3. API REQUEST/RESPONSE EXAMPLES

### 3.1 Start Debate

**Request**:
```http
POST /debates HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "topic": "Should social media platforms be held liable for user content?",
  "rounds": 2,
  "use_internet": true
}
```

**Response**:
```json
{
  "debate_id": "d7f3a2b1-4c5e-6789-abcd-ef0123456789",
  "topic": "Should social media platforms be held liable for user content?",
  "domain": "technology",
  "status": "created"
}
```

### 3.2 Send Turn

**Request**:
```http
POST /debates/d7f3a2b1-4c5e-6789-abcd-ef0123456789/turns HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "generate_ai": true
}
```

**Response**:
```json
{
  "pro_argument": "Section 230 was written in 1996, when 'social media' meant AOL chat rooms. Today, these platforms algorithmically amplify harmful content for profit. When Facebook's own research showed Instagram harms teen mental health, they buried it. That's not neutral hosting—that's active harm. Newspapers are liable for what they print. TV stations are liable for what they broadcast. Why should tech giants get special immunity while profiting from rage and misinformation? Liability creates accountability. Without it, there's no incentive to change.",
  "con_argument": "My opponent wants to kill the internet as we know it. Without Section 230, every platform would face lawsuits for every user post. Small sites couldn't exist. Only giants like Facebook could afford the legal teams. And what's the alternative? Pre-screening every post? That's censorship at scale. The cure is worse than the disease. Yes, platforms make mistakes. But the solution is transparency requirements and algorithm audits—not making them liable for the speech of billions of users they can't possibly monitor.",
  "round_num": 1,
  "is_complete": false
}
```

### 3.3 Score Debate

**Request**:
```http
POST /debates/d7f3a2b1-4c5e-6789-abcd-ef0123456789/score HTTP/1.1
Host: localhost:8000
```

**Response**:
```json
{
  "pro_score": 76,
  "con_score": 79,
  "winner": "con",
  "reasoning": "Con wins with a score of 79 to 76. While Pro made strong points about platform accountability and algorithmic amplification, Con effectively countered with practical concerns about implementation. Con's argument about small platforms and censorship resonated as a more realistic assessment of liability consequences. Both sides used evidence well, but Con's framing of 'the cure being worse than the disease' was more persuasive.",
  "fact_check": {
    "pro": {
      "faithfulness_score": 0.68,
      "verdict": "partially_supported"
    },
    "con": {
      "faithfulness_score": 0.72,
      "verdict": "well_supported"
    }
  }
}
```

### 3.4 Health Check

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "gpu_memory_used_gb": 11.8,
  "gpu_memory_total_gb": 24.0,
  "adapters_available": ["education", "medicine", "ecology", "technology", "debate"]
}
```

### 3.5 Stream Turn (SSE)

**Request**:
```http
POST /debates/d7f3a2b1-4c5e-6789-abcd-ef0123456789/turns/stream HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "generate_ai": true
}
```

**Response** (Server-Sent Events):
```
data: {"type": "start", "stance": "pro"}

data: {"type": "token", "content": "Here's"}

data: {"type": "token", "content": " a"}

data: {"type": "token", "content": " question"}

data: {"type": "token", "content": " for"}

...

data: {"type": "complete", "stance": "pro", "full_argument": "Here's a question for everyone..."}

data: {"type": "start", "stance": "con"}

...

data: {"type": "complete", "stance": "con", "full_argument": "My opponent paints..."}

data: {"done": true}
```

---

## 4. OUTPUT ARTIFACTS

### 4.1 Debate Result JSON

**File**: `runs/debates/20260111_143022_should_electric_vehicles/result.json`

```json
{
  "topic": "Should electric vehicles be mandatory by 2035?",
  "domain": "technology",
  "rounds": 2,
  "pro_arguments": [
    "Here's a question for everyone in this room: how many of you have breathed smog-filled air this year?...",
    "My opponent asks 'who pays?' Let me answer directly..."
  ],
  "con_arguments": [
    "My opponent paints a rosy picture, but let me bring us back to reality...",
    "Let's examine that 'price parity by 2027' claim..."
  ],
  "research_context": "Electric vehicle (EV) is a vehicle that uses one or more electric motors...",
  "host_introduction": "Good evening and welcome to tonight's debate!...",
  "fact_check": {
    "pro": {
      "num_claims": 12,
      "supported_claims": 9,
      "faithfulness_score": 0.75,
      "verdict": "well_supported"
    },
    "con": {
      "num_claims": 11,
      "supported_claims": 7,
      "faithfulness_score": 0.64,
      "verdict": "partially_supported"
    }
  },
  "judge_score": {
    "pro_score": 82,
    "con_score": 73,
    "winner": "pro",
    "reasoning": "Pro wins with a score of 82 to 73..."
  },
  "recommended_guests": [
    {
      "name": "Mary Nichols",
      "title": "Former Chair, California Air Resources Board",
      "expertise": "Environmental regulation and EV policy",
      "relevance": "Key architect of California's zero-emission vehicle mandate"
    }
  ],
  "duration_seconds": 52.3,
  "use_internet": true,
  "timestamp": "20260111_143022"
}
```

### 4.2 Debate Transcript

**File**: `runs/debates/20260111_143022_should_electric_vehicles/transcript.txt`

```
================================================================================
DEBATE TRANSCRIPT
================================================================================

Topic: Should electric vehicles be mandatory by 2035?
Domain: technology
Date: 2026-01-11 14:30:22
Rounds: 2

--------------------------------------------------------------------------------
HOST INTRODUCTION
--------------------------------------------------------------------------------

Good evening and welcome to tonight's debate! Our topic: Should electric
vehicles be mandatory by 2035?

This is a question that affects millions of drivers, automakers, and the
future of our planet. With EV sales growing 35% in 2025 and climate
pressure mounting, the stakes couldn't be higher.

Tonight's key questions:
• Can the power grid handle universal EV adoption?
• What about rural communities without charging infrastructure?
• Is the environmental benefit real when considering battery production?
• Should governments mandate or let markets decide?
• Who wins and who loses under EV mandates?

Let's begin!

--------------------------------------------------------------------------------
ROUND 1
--------------------------------------------------------------------------------

[PRO - Opening Statement]

Here's a question for everyone in this room: how many of you have breathed
smog-filled air this year? The answer is all of us, and that's exactly why
we need EV mandates by 2035. The numbers speak for themselves—EV sales
jumped 35% last year alone, proving that people WANT this change. They just
need the push. And let's talk about the elephant in the room: climate change
isn't waiting for market forces. We have twelve years. Twelve. EVs produce
zero tailpipe emissions and are already approaching price parity with gas
guzzlers. Yes, infrastructure needs work—but that's exactly what mandates
drive: investment, innovation, jobs. The auto industry transformed before,
and it will transform again. The only question is whether we lead that
transformation or get left behind. I say we lead.

[CON - Opening Statement]

My opponent paints a rosy picture, but let me bring us back to reality. Who
pays for this green dream? Not the wealthy—they can afford any car they want.
It's working families, rural communities, and small business owners who'll
bear the burden. You heard the statistic: 60% of EV sales are in China. Why?
Because they have the infrastructure and subsidies we don't. Here in America,
try finding a charging station in rural Montana or West Virginia. Now imagine
telling a farmer their truck is illegal. The inconvenient truth about EVs?
Their batteries require lithium, cobalt, and rare earth minerals mined under
questionable conditions. We're trading one environmental problem for another.
Market forces are already driving EV adoption—35% growth without mandates!
Why rush a mandate that punishes the poor and rewards the privileged?

--------------------------------------------------------------------------------
ROUND 2
--------------------------------------------------------------------------------

[PRO - Rebuttal]

My opponent asks "who pays?" Let me answer directly: we ALL pay if we don't
act. The cost of climate inaction—floods, droughts, wildfires—dwarfs any EV
transition costs. But here's what they conveniently ignored: price parity is
coming in 2027, just two years away. After that, EVs will be CHEAPER than
gas cars. The "burden on working families" argument dissolves when EVs cost
less to buy AND operate. As for rural infrastructure—that's precisely why we
need mandates! Mandates create certainty, certainty attracts investment,
investment builds charging networks. It happened with electricity, with
telephones, with internet. And the battery supply chain? We're already
developing sodium-ion and solid-state alternatives that don't need cobalt.
Innovation follows demand. Give the market a clear signal, and it delivers.

[CON - Rebuttal]

Let's examine that "price parity by 2027" claim. That's a Bloomberg
projection, not a guarantee. Two years ago, they said it would be 2025.
Projections change, but mandates don't. Once you criminalize gas cars, there's
no going back if those projections are wrong. And speaking of infrastructure
investment—who's paying for it? Taxpayers. We're talking about a trillion
dollars to build out charging networks. That's money not going to schools,
hospitals, or housing. My opponent talks about "certainty attracting
investment." You know what else creates certainty? Prison. Mandates aren't
inspiration—they're coercion. The 35% growth they keep citing proves my
point: the market IS working. Consumers ARE choosing EVs. Why do we need
government forcing the issue when freedom is already delivering results?

--------------------------------------------------------------------------------
FACT-CHECK SUMMARY
--------------------------------------------------------------------------------

PRO Side:
  Claims analyzed: 12
  Claims supported: 9 (75%)
  Verdict: WELL SUPPORTED

CON Side:
  Claims analyzed: 11
  Claims supported: 7 (64%)
  Verdict: PARTIALLY SUPPORTED

--------------------------------------------------------------------------------
FINAL JUDGMENT
--------------------------------------------------------------------------------

SCORES:
  PRO: 82 points
  CON: 73 points

WINNER: PRO

REASONING:
Pro wins with a score of 82 to 73. Pro's arguments were better supported by
evidence, particularly the statistics on EV growth and price parity projections.
While Con raised valid concerns about infrastructure and equity, several claims
lacked specific data support. Pro demonstrated stronger use of logical connectors
and maintained a more consistent evidence-based approach throughout the debate.

--------------------------------------------------------------------------------
RECOMMENDED GUESTS
--------------------------------------------------------------------------------

1. Mary Nichols
   Former Chair, California Air Resources Board
   Expertise: Environmental regulation and EV policy
   Relevance: Key architect of California's zero-emission vehicle mandate

2. Sandy Munro
   Automotive Engineer and Manufacturing Analyst
   Expertise: EV manufacturing, teardown analysis, cost optimization
   Relevance: Provides detailed comparisons of EV vs ICE manufacturing

3. Daniel Sperling
   Professor, UC Davis; Founding Director, ITS-Davis
   Expertise: Transportation technology and policy
   Relevance: Leading academic researcher on sustainable transportation

4. Michael Liebreich
   Founder, BloombergNEF
   Expertise: Clean energy finance and market analysis
   Relevance: Created the data source most cited in EV market projections

================================================================================
END OF TRANSCRIPT
================================================================================
```

---

## 5. TROUBLESHOOTING GUIDE

### 5.1 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `CUDA out of memory` | Not enough GPU VRAM | Reduce batch size or use single model |
| `Model not found at path` | Missing base model | Download model to `models/base/` |
| `Adapter not found` | Missing trained adapter | Train adapter or use `--no-adapter` |
| `Connection refused` | Server not running | Start server with `python scripts/run_server.py` |
| `Wikipedia API error` | Rate limiting | Add delay between requests |
| `DuckDuckGo timeout` | Network issues | Retry or disable internet search |

### 5.2 Memory Optimization

**For 8GB VRAM GPUs**:
```python
# Use single model instead of dual
crew = DebateCrew(use_dual_model=False)

# Reduce max tokens
debate_tool = DebateGenerationTool(max_tokens=150)

# Clear cache between debates
torch.cuda.empty_cache()
```

**For CPU-only**:
```python
# Load model on CPU (very slow)
model, tokenizer = load_base_model(device_map="cpu")
```

### 5.3 Quality Issues

**If arguments are too short**:
- Increase `max_tokens` in generation
- Check that research context is being passed

**If arguments contain artifacts**:
- Verify `_clean_output()` is being called
- Check prompt formatting

**If research quality is low**:
- Enable internet search (`--use-internet`)
- Increase refinement retries

---

## 6. PERFORMANCE BENCHMARKS

### 6.1 Debate Generation Time

| Configuration | Time per Debate | GPU Memory |
|---------------|-----------------|------------|
| Single model, no internet | 25-35 sec | ~6 GB |
| Dual model, no internet | 35-50 sec | ~12 GB |
| Dual model + internet | 45-70 sec | ~12 GB |
| Dual model + internet + guests | 60-90 sec | ~12 GB |

### 6.2 Training Benchmarks

| Dataset Size | Training Time | Final Perplexity |
|--------------|---------------|------------------|
| 500 examples | ~10 min | 4.5-5.0 |
| 1000 examples | ~20 min | 4.0-4.5 |
| 2000 examples | ~40 min | 3.5-4.0 |

### 6.3 API Response Times

| Endpoint | Average Response Time |
|----------|----------------------|
| `GET /health` | < 50 ms |
| `POST /debates` | 500-1000 ms |
| `POST /debates/:id/turns` | 3-8 sec |
| `POST /debates/:id/score` | 200-500 ms |

---

## 7. CONFIGURATION REFERENCE

### 7.1 Environment Variables

```bash
# Python Backend
CUDA_VISIBLE_DEVICES=0           # GPU selection
HF_HOME=/path/to/cache           # HuggingFace cache directory
TRANSFORMERS_CACHE=/path/to/cache

# Node.js Backend
OPENROUTER_API_KEY=sk-or-xxx     # Required for cloud LLM
OPENROUTER_MODEL=nvidia/nemotron-nano-9b-v2:free
DATABASE_URL=file:./dev.db

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false
```

### 7.2 Debate Configuration Options

```python
# DebateCrew initialization
crew = DebateCrew(
    use_internet=True,              # Enable web search
    output_dir=Path("runs/debates"), # Output directory
    verbose=True,                   # Print progress
)

# run_debate() options
result = crew.run_debate(
    topic="Your topic",
    num_rounds=2,                   # 1-5 recommended
    recommend_guests=True,          # Find expert recommendations
    progress_callback=callback,     # UI progress updates
)
```

### 7.3 Training Configuration Options

```python
training_args = get_training_arguments(
    output_dir="models/adapters/custom",
    num_epochs=3,                   # Training epochs
    batch_size=4,                   # Per-device batch size
    gradient_accumulation_steps=4,  # Effective batch = 16
    learning_rate=2e-4,             # Peak LR
    warmup_ratio=0.1,               # 10% warmup
    logging_steps=10,               # Log every 10 steps
    eval_steps=50,                  # Evaluate every 50 steps
    save_steps=100,                 # Checkpoint every 100 steps
)

lora_config = get_lora_config(
    r=16,                           # LoRA rank
    lora_alpha=32,                  # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Attention layers
    lora_dropout=0.05,              # Regularization
)
```

---

## SUMMARY

This documentation suite provides complete coverage of the Debate Simulator Nomotron project:

| Document | Contents |
|----------|----------|
| **DETAILED_PROJECT_EXPLICATION.md** | Overview, architecture, quick start |
| **DETAILED_PROJECT_EXPLICATION_CREWAI.md** | Complete CrewAI system deep-dive |
| **DETAILED_PROJECT_EXPLICATION_BACKEND.md** | Python backend, training, API |
| **DETAILED_PROJECT_EXPLICATION_FRONTEND.md** | React frontend, Node.js alternative |
| **DETAILED_PROJECT_EXPLICATION_EXAMPLES.md** | Full examples, artifacts, troubleshooting |

The project represents a production-ready multi-agent debate system with:
- ✅ 11 specialized CrewAI agents
- ✅ Dual model architecture for parallel generation
- ✅ Dynamic LoRA adapter loading
- ✅ Quality refinement loops for research
- ✅ Comprehensive fact-checking and judging
- ✅ Full-stack web application
- ✅ Complete training pipeline
- ✅ Docker deployment support

---

*Generated: 2026-01-11*
*Project: Debate Simulator Nomotron*
*Documentation Version: 1.0*
