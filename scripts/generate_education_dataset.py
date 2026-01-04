#!/usr/bin/env python3
"""
Phase 2: Education Domain Dataset Generation

Creates a local dataset for debate turn generation in the education domain.
Format: JSONL with fields (domain, topic, stance, context, output)

Features:
- Deterministic splits (fixed seed for reproducibility)
- 80/10/10 train/val/test split
- Diverse education topics

Run from project root:
    python scripts/generate_education_dataset.py
"""

import json
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

SEED = 42  # Fixed seed for reproducibility

@dataclass
class DebateTurn:
    domain: str
    topic: str
    stance: str  # "pro" or "con"
    context: str  # Previous debate context or background
    output: str  # The debate argument to generate


# Education domain debate topics with pro/con arguments
EDUCATION_DEBATES = [
    {
        "topic": "Should standardized testing be the primary method of student assessment?",
        "pro_args": [
            "Standardized tests provide objective, comparable metrics across different schools and districts, ensuring fair evaluation of student performance regardless of their background or location.",
            "These assessments help identify learning gaps early, allowing educators to intervene with targeted support before students fall too far behind their peers.",
            "Standardized testing holds schools accountable for educational outcomes, incentivizing improvement in underperforming institutions and ensuring minimum quality standards.",
            "Universities and employers need reliable metrics for comparing applicants; standardized tests provide a common benchmark that transcends grade inflation and varying school quality.",
            "The structured nature of standardized tests teaches students valuable skills: time management, working under pressure, and following precise instructions."
        ],
        "con_args": [
            "Standardized tests measure a narrow range of cognitive abilities, failing to capture creativity, critical thinking, collaboration skills, and emotional intelligence that are crucial for success.",
            "Teaching to the test narrows curriculum, forcing educators to abandon enriching activities like arts, physical education, and project-based learning in favor of test preparation.",
            "These tests create excessive stress and anxiety in students, particularly affecting younger children and those with test anxiety, potentially causing lasting psychological harm.",
            "Standardized testing perpetuates socioeconomic inequalities since wealthier families can afford test preparation services, tutoring, and educational resources unavailable to disadvantaged students.",
            "A single test score cannot capture a student's growth, effort, or potential; it provides merely a snapshot that may be affected by illness, personal circumstances, or testing conditions."
        ]
    },
    {
        "topic": "Should homework be abolished in primary education?",
        "pro_args": [
            "Research shows homework in primary school has minimal academic benefit; young children learn better through play, exploration, and family interaction than repetitive worksheets.",
            "Homework creates unnecessary stress for young children and their families, leading to conflicts at home and negative associations with learning during formative years.",
            "Children need unstructured time for physical activity, creative play, and social development; homework steals these essential hours from their after-school lives.",
            "Homework disadvantages children from families unable to provide help, quiet study spaces, or educational resources, widening the achievement gap based on home circumstances.",
            "Primary school children already spend 6-7 hours in structured learning; additional homework leads to burnout and can extinguish natural curiosity and love of learning."
        ],
        "con_args": [
            "Homework reinforces classroom learning through practice, helping students consolidate knowledge and develop automaticity in foundational skills like reading and mathematics.",
            "Regular homework establishes study habits and self-discipline that become essential for academic success in later years; starting early builds these crucial skills.",
            "Homework provides parents visibility into their child's education, creating opportunities for involvement and enabling them to identify and address learning difficulties.",
            "Some children need additional practice time beyond classroom hours to master concepts; homework provides this necessary extended learning opportunity.",
            "Homework teaches time management and responsibility, preparing children for the increasing academic demands they will face as they progress through education."
        ]
    },
    {
        "topic": "Should universities adopt fully online degree programs?",
        "pro_args": [
            "Online education democratizes access to higher learning, allowing students from remote areas, working adults, and those with disabilities to earn degrees they otherwise couldn't pursue.",
            "Digital learning reduces costs significantly - no commuting, no relocation, often lower tuition - making higher education financially accessible to more people.",
            "Online programs offer flexibility that accommodates diverse life circumstances, enabling students to balance education with work, caregiving, or other responsibilities.",
            "Students can learn at their own pace, rewatching lectures and spending more time on difficult concepts, leading to better mastery of material for many learners.",
            "Online education prepares students for the modern workforce where remote collaboration, digital communication, and self-directed work are increasingly essential skills."
        ],
        "con_args": [
            "Campus-based education provides invaluable face-to-face interactions, mentorship opportunities, and networking that significantly impact career prospects and personal development.",
            "Many disciplines require hands-on learning - laboratory work, clinical practice, studio arts - that cannot be adequately replicated in an online environment.",
            "Online learning requires exceptional self-motivation and discipline; many students struggle without the structure and accountability of traditional classroom settings.",
            "The social experience of university - clubs, sports, dormitory life, in-person discussions - contributes fundamentally to personal growth and cannot be replicated online.",
            "Online degrees still face credibility questions from employers who may perceive them as less rigorous than traditional programs, potentially limiting graduates' opportunities."
        ]
    },
    {
        "topic": "Should coding be mandatory in K-12 curriculum?",
        "pro_args": [
            "Digital literacy is as fundamental as reading and math in the 21st century; coding teaches logical thinking and problem-solving that apply across all disciplines.",
            "Early exposure to programming opens doors to high-paying technology careers and helps address the growing skills gap in the tech industry.",
            "Learning to code teaches computational thinking - breaking complex problems into smaller steps - a valuable skill applicable far beyond programming itself.",
            "Students who understand how software works become informed digital citizens, better equipped to navigate issues of privacy, security, and technology ethics.",
            "Coding integrates well with other subjects, making abstract concepts in math and science tangible through interactive simulations and data analysis projects."
        ],
        "con_args": [
            "Mandating coding displaces other subjects; an already crowded curriculum cannot infinitely expand, and coding may come at the expense of humanities, arts, or physical education.",
            "Not all students need programming skills; many successful careers require no coding, and mandatory courses may frustrate students whose interests and aptitudes lie elsewhere.",
            "Quality coding education requires trained teachers and technology infrastructure that many schools lack; unfunded mandates create inequality rather than opportunity.",
            "Coding languages and platforms change rapidly; specific skills taught today may be obsolete by the time students enter the workforce, unlike timeless fundamentals.",
            "Computational thinking can be taught through existing subjects like mathematics and science without adding another mandatory course to students' already heavy workloads."
        ]
    },
    {
        "topic": "Should teachers be evaluated primarily based on student test scores?",
        "pro_args": [
            "Student outcomes are the ultimate measure of teaching effectiveness; test scores provide objective data to identify successful teachers and those needing improvement.",
            "Performance-based evaluation creates accountability and incentivizes teachers to continuously improve their practice and focus on student learning.",
            "Data-driven evaluation removes subjective bias from performance reviews, ensuring fair assessment regardless of personal relationships with administrators.",
            "Identifying effective teachers through outcomes data allows schools to replicate successful practices and provide mentorship opportunities.",
            "Parents and taxpayers deserve accountability in education spending; measurable student progress demonstrates return on educational investment."
        ],
        "con_args": [
            "Test scores reflect many factors beyond teacher quality: student home environment, prior learning, socioeconomic status, and school resources all significantly impact results.",
            "Tying evaluation to test scores incentivizes teaching to the test, narrowing curriculum and discouraging the deeper learning that assessments cannot measure.",
            "Great teaching includes building relationships, inspiring curiosity, supporting emotional development, and fostering critical thinking - none of which standardized tests capture.",
            "Score-based evaluation disadvantages teachers who work with challenging populations, driving talented educators away from the students who need them most.",
            "The stress of high-stakes evaluation based on student scores contributes to teacher burnout and departure from the profession, worsening teacher shortages."
        ]
    },
    {
        "topic": "Should student loan debt be forgiven?",
        "pro_args": [
            "Crushing student debt prevents graduates from buying homes, starting families, and contributing to economic growth; forgiveness would unleash significant economic activity.",
            "Higher education was once affordable; the explosion of tuition costs and predatory lending has trapped a generation in debt they were told was necessary for success.",
            "Student loan forgiveness would disproportionately help minorities and first-generation students who borrowed more and have fewer family resources to repay loans.",
            "Many borrowers were teenagers when taking on massive debt with limited understanding of long-term implications; predatory practices justify relief.",
            "Investing in an educated population benefits society broadly through innovation, civic participation, and economic productivity; the collective benefit justifies collective investment."
        ],
        "con_args": [
            "Loan forgiveness is regressive, benefiting those with college degrees who already have higher earning potential, while those who never attended or completed college receive nothing.",
            "Borrowers made voluntary agreements to repay loans; forgiveness rewards those who borrowed irresponsibly while those who sacrificed to repay get nothing.",
            "Without addressing underlying tuition costs, forgiveness creates moral hazard and expectations of future forgiveness, encouraging continued irresponsible borrowing and spending.",
            "The cost of mass forgiveness would be borne by all taxpayers, including those who chose not to attend college, paid their loans, or attended affordable schools.",
            "Better solutions exist: income-driven repayment, targeted forgiveness for public service, or addressing the root causes of educational cost inflation."
        ]
    },
    {
        "topic": "Should schools implement year-round education?",
        "pro_args": [
            "The traditional summer break causes significant learning loss, particularly for disadvantaged students; year-round schooling maintains academic momentum and reduces achievement gaps.",
            "Distributing breaks throughout the year prevents burnout for both students and teachers, providing regular recovery periods without the extended summer disruption.",
            "Year-round schooling allows more efficient use of school facilities, which otherwise sit empty for months; this represents better return on infrastructure investment.",
            "Working parents struggle to find childcare for extended summer breaks; distributed shorter breaks are more manageable for family scheduling and reduce summer learning camp costs.",
            "Many countries with superior educational outcomes use year-round or extended school year models, suggesting this approach produces better results."
        ],
        "con_args": [
            "Summer break allows students time for enrichment activities, camps, internships, family travel, and unstructured learning that structured schooling cannot provide.",
            "Research on year-round schooling shows mixed results; the model's benefits are not clearly established enough to justify disrupting established traditions and systems.",
            "Year-round schooling creates childcare and scheduling challenges for families during multiple shorter breaks instead of one extended summer period.",
            "The summer break is culturally significant, supporting family traditions, summer employment for teens, and the camp and recreation industry that employs many educators.",
            "Teachers rely on summer for professional development, advanced education, and recuperation from the demands of teaching; shorter scattered breaks provide insufficient time for these activities."
        ]
    },
    {
        "topic": "Should schools ban mobile phones entirely?",
        "pro_args": [
            "Phones are a constant distraction; studies show their mere presence reduces cognitive capacity, and bans immediately improve attention and academic performance.",
            "Social media accessed via phones contributes to cyberbullying, anxiety, depression, and social comparison that harm students' mental health and school climate.",
            "Phone bans promote face-to-face interaction and relationship building during breaks, restoring social skills that constant device use has eroded.",
            "Without phones, students engage more deeply in classroom discussions and activities, benefiting from the focused learning environment that schools should provide.",
            "Schools cannot effectively police appropriate vs. inappropriate phone use; a complete ban is easier to enforce and removes constant negotiation with students."
        ],
        "con_args": [
            "Phones are essential safety tools allowing students to contact parents in emergencies; bans create anxiety for both students and families.",
            "Rather than banning technology, schools should teach digital citizenship and self-regulation skills students will need throughout their lives.",
            "Phones have legitimate educational uses - research, educational apps, documentation of work, accessibility features - that benefit learning when properly integrated.",
            "Bans are difficult to enforce and create adversarial relationships between students and staff; energy spent on enforcement could better serve education.",
            "Students need to learn to manage technology distractions in environments where phones exist; artificial phone-free zones don't prepare them for the real world."
        ]
    },
    {
        "topic": "Should universities use affirmative action in admissions?",
        "pro_args": [
            "Historical discrimination created systemic disadvantages that persist today; affirmative action helps counterbalance ongoing effects of past injustice.",
            "Diverse student bodies enhance educational quality for all students, exposing them to different perspectives and better preparing them for diverse workplaces and society.",
            "Without active intervention, unconscious biases in admissions perpetuate homogeneity; affirmative action provides a necessary counterweight to these invisible barriers.",
            "Students from underrepresented backgrounds who succeed at selective universities become role models and community leaders, creating positive cycles for future generations.",
            "Merit cannot be measured solely by grades and test scores, which reflect educational opportunity; considering context produces a more complete picture of potential."
        ],
        "con_args": [
            "Admissions should be based solely on individual achievement and potential; considering race or ethnicity is inherently discriminatory regardless of intent.",
            "Affirmative action can place students in institutions where they struggle academically, leading to higher dropout rates and frustration rather than success.",
            "Race-based preferences stigmatize their intended beneficiaries, leading peers to question whether qualified individuals earned their positions through merit.",
            "Socioeconomic-based preferences would help disadvantaged students of all backgrounds while avoiding the legal and ethical complications of racial classification.",
            "Affirmative action at elite universities helps primarily middle-class minorities while ignoring the deeper K-12 educational inequities that create opportunity gaps."
        ]
    },
    {
        "topic": "Should AI tutoring systems replace human tutors?",
        "pro_args": [
            "AI tutors provide unlimited availability and infinite patience, offering help at any hour without frustration, ideal for students who need extensive practice.",
            "Personalized AI systems can adapt to each student's learning pace, style, and knowledge gaps, providing customization that human tutors cannot achieve at scale.",
            "AI tutoring dramatically reduces costs, making personalized educational support accessible to families who cannot afford expensive human tutors.",
            "AI systems can instantly access vast knowledge bases and provide consistent, accurate information without the variability inherent in human expertise.",
            "Students may feel less embarrassed asking AI systems repeated questions or admitting confusion, removing social barriers to seeking help."
        ],
        "con_args": [
            "Human tutors provide emotional support, encouragement, and mentorship that AI cannot replicate; learning is as much emotional as cognitive.",
            "AI systems lack the intuition to recognize when a student is frustrated, confused, or needs a different approach; human tutors read these cues naturally.",
            "The relationship with a caring human tutor motivates students and builds confidence in ways that interactions with software cannot achieve.",
            "AI tutors may reinforce existing misconceptions or provide explanations that work technically but don't connect with a student's existing understanding.",
            "Over-reliance on AI tutoring may reduce human interaction skills and comfort with asking for help from people, important abilities for future success."
        ]
    },
]


def create_context_variations(topic: str) -> list[str]:
    """Generate different context variations for a debate topic."""
    return [
        f"You are participating in an academic debate on the topic: {topic}",
        f"In a formal debate setting, address the following motion: {topic}",
        f"Prepare a compelling argument for a debate competition. Topic: {topic}",
        f"As a debate team member, construct an argument regarding: {topic}",
        f"Present a well-reasoned position in this educational debate: {topic}",
    ]


def generate_dataset() -> list[DebateTurn]:
    """Generate complete dataset from debate topics."""
    dataset = []

    for debate in EDUCATION_DEBATES:
        topic = debate["topic"]
        contexts = create_context_variations(topic)

        # Generate pro arguments
        for i, arg in enumerate(debate["pro_args"]):
            context = contexts[i % len(contexts)]
            dataset.append(DebateTurn(
                domain="education",
                topic=topic,
                stance="pro",
                context=context,
                output=arg
            ))

        # Generate con arguments
        for i, arg in enumerate(debate["con_args"]):
            context = contexts[i % len(contexts)]
            dataset.append(DebateTurn(
                domain="education",
                topic=topic,
                stance="con",
                context=context,
                output=arg
            ))

    return dataset


def split_dataset(
    dataset: list[DebateTurn],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = SEED
) -> tuple[list[DebateTurn], list[DebateTurn], list[DebateTurn]]:
    """
    Split dataset into train/val/test with deterministic randomization.

    Uses stratified splitting to ensure balanced stance distribution.
    """
    random.seed(seed)

    # Shuffle deterministically
    shuffled = dataset.copy()
    random.shuffle(shuffled)

    n = len(shuffled)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train = shuffled[:train_end]
    val = shuffled[train_end:val_end]
    test = shuffled[val_end:]

    return train, val, test


def save_jsonl(data: list[DebateTurn], path: Path):
    """Save dataset to JSONL format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        for item in data:
            f.write(json.dumps(asdict(item)) + '\n')


def compute_stats(data: list[DebateTurn]) -> dict:
    """Compute statistics for a dataset split."""
    pro_count = sum(1 for d in data if d.stance == "pro")
    con_count = sum(1 for d in data if d.stance == "con")
    topics = set(d.topic for d in data)

    return {
        "total": len(data),
        "pro": pro_count,
        "con": con_count,
        "unique_topics": len(topics),
        "avg_output_length": sum(len(d.output) for d in data) / len(data) if data else 0,
    }


def main():
    print("=" * 60)
    print("PHASE 2: Education Domain Dataset Generation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Random seed: {SEED}")

    # Generate dataset
    print("\n--- Generating Dataset ---")
    dataset = generate_dataset()
    print(f"Total samples generated: {len(dataset)}")

    # Split dataset
    print("\n--- Splitting Dataset (80/10/10) ---")
    train, val, test = split_dataset(dataset)

    # Save splits
    splits_dir = DATA_DIR / "splits" / "education"
    save_jsonl(train, splits_dir / "train.jsonl")
    save_jsonl(val, splits_dir / "val.jsonl")
    save_jsonl(test, splits_dir / "test.jsonl")

    print(f"Saved to: {splits_dir}")

    # Print statistics
    print("\n--- Dataset Statistics ---")
    for name, data in [("Train", train), ("Validation", val), ("Test", test)]:
        stats = compute_stats(data)
        print(f"\n{name}:")
        print(f"  Samples: {stats['total']}")
        print(f"  Pro/Con: {stats['pro']}/{stats['con']}")
        print(f"  Unique topics: {stats['unique_topics']}")
        print(f"  Avg output length: {stats['avg_output_length']:.1f} chars")

    # Save metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "seed": SEED,
        "domain": "education",
        "splits": {
            "train": compute_stats(train),
            "val": compute_stats(val),
            "test": compute_stats(test),
        },
        "topics": list(set(d.topic for d in dataset)),
    }

    with open(splits_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nMetadata saved to: {splits_dir / 'metadata.json'}")

    # Show sample
    print("\n--- Sample Data ---")
    sample = train[0]
    print(f"Domain: {sample.domain}")
    print(f"Topic: {sample.topic}")
    print(f"Stance: {sample.stance}")
    print(f"Context: {sample.context}")
    print(f"Output: {sample.output[:200]}...")

    print("\n✓ Dataset generation complete!")


if __name__ == "__main__":
    main()
