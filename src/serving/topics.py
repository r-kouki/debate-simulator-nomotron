"""
Topic data and search functionality for the debate simulator API.

Provides debate topics with searchable metadata.
"""

import re
from dataclasses import dataclass
from src.serving.models import TopicSummary, TopicDetail, TopicSearchResponse


# Comprehensive debate topics database
TOPICS: list[dict] = [
    {
        "id": "standardized-testing",
        "title": "Should standardized testing be the primary method of student assessment?",
        "category": "Education",
        "summary": "Debate over using standardized tests vs alternative assessment methods in schools.",
        "description": "Standardized testing has been a cornerstone of educational assessment for decades, providing comparable metrics across schools and districts. However, critics argue these tests narrow curriculum and create undue stress while failing to measure crucial skills like creativity and collaboration.",
        "key_points": ["Objective measurement", "Curriculum impact", "Student stress", "Equity concerns"],
        "pros": [
            "Provides objective, comparable metrics across schools",
            "Identifies learning gaps early for intervention",
            "Holds schools accountable for outcomes",
            "Offers reliable benchmarks for college admissions"
        ],
        "cons": [
            "Narrows curriculum to test preparation",
            "Creates excessive stress and anxiety",
            "Perpetuates socioeconomic inequalities",
            "Fails to measure creativity and critical thinking"
        ],
        "fallacies": ["False dilemma (tests vs no assessment)", "Appeal to tradition"],
        "sources": ["National Education Association", "Educational Testing Service reports"]
    },
    {
        "id": "homework-primary",
        "title": "Should homework be abolished in primary education?",
        "category": "Education",
        "summary": "Examining whether homework helps or harms young students' learning and development.",
        "description": "Research on homework effectiveness shows mixed results for primary students. While some argue it reinforces learning and builds study habits, others contend it creates stress, reduces family time, and has minimal academic benefit for young children.",
        "key_points": ["Academic benefit", "Family time", "Stress levels", "Equity"],
        "pros": [
            "Young children learn better through play and exploration",
            "Reduces stress for children and families",
            "Allows time for physical activity and creativity",
            "Eliminates homework-based achievement gaps"
        ],
        "cons": [
            "Homework reinforces classroom learning",
            "Builds study habits and self-discipline early",
            "Provides parent visibility into education",
            "Prepares students for future academic demands"
        ],
        "fallacies": ["Slippery slope", "Appeal to nature"],
        "sources": ["Harris Cooper meta-analysis", "OECD education reports"]
    },
    {
        "id": "online-degrees",
        "title": "Should universities adopt fully online degree programs?",
        "category": "Education",
        "summary": "The future of higher education: online learning vs traditional campus experience.",
        "description": "Online education democratizes access and reduces costs, but questions remain about quality, social development, and employer acceptance. The pandemic accelerated this shift, forcing a reevaluation of what college education means.",
        "key_points": ["Accessibility", "Cost reduction", "Social experience", "Employer perception"],
        "pros": [
            "Democratizes access to higher education globally",
            "Significantly reduces costs for students",
            "Offers flexibility for working adults",
            "Prepares students for remote work environments"
        ],
        "cons": [
            "Loses valuable face-to-face mentorship",
            "Cannot replicate hands-on learning experiences",
            "Reduces social and networking opportunities",
            "May face employer credibility questions"
        ],
        "fallacies": ["False equivalence", "Appeal to novelty"],
        "sources": ["Chronicle of Higher Education", "Inside Higher Ed research"]
    },
    {
        "id": "mandatory-coding",
        "title": "Should coding be mandatory in K-12 curriculum?",
        "category": "Education",
        "summary": "Is computer science education essential for all students in the digital age?",
        "description": "Digital literacy is increasingly important in modern society. Proponents argue coding teaches computational thinking applicable across disciplines, while critics question whether mandatory programming displaces other valuable subjects.",
        "key_points": ["Digital literacy", "Career preparation", "Curriculum space", "Teacher readiness"],
        "pros": [
            "Teaches logical thinking and problem-solving",
            "Opens doors to high-paying tech careers",
            "Creates informed digital citizens",
            "Integrates well with math and science"
        ],
        "cons": [
            "Displaces arts, humanities, or physical education",
            "Not all students need programming skills",
            "Requires significant teacher training investment",
            "Coding languages become obsolete quickly"
        ],
        "fallacies": ["Appeal to modernity", "Bandwagon fallacy"],
        "sources": ["Code.org research", "ACM K-12 CS Framework"]
    },
    {
        "id": "teacher-test-evaluation",
        "title": "Should teachers be evaluated primarily based on student test scores?",
        "category": "Education",
        "summary": "Using student performance data to assess teacher effectiveness.",
        "description": "Performance-based teacher evaluation promises accountability but faces criticism for oversimplifying teaching quality. Critics argue test scores reflect many factors beyond teacher skill, while proponents see data as essential for improvement.",
        "key_points": ["Accountability", "Measurement validity", "Teacher morale", "Student factors"],
        "pros": [
            "Provides objective accountability measures",
            "Incentivizes focus on student outcomes",
            "Removes subjective bias from evaluations",
            "Identifies effective practices to replicate"
        ],
        "cons": [
            "Test scores reflect many non-teacher factors",
            "Encourages teaching to the test",
            "Ignores unmeasurable teaching qualities",
            "Drives teachers away from challenging schools"
        ],
        "fallacies": ["Oversimplification", "Correlation vs causation"],
        "sources": ["RAND Corporation studies", "American Educational Research Association"]
    },
    {
        "id": "student-loan-forgiveness",
        "title": "Should student loan debt be forgiven?",
        "category": "Policy",
        "summary": "Addressing the $1.7 trillion student debt crisis through forgiveness programs.",
        "description": "Student debt affects major life decisions for millions of Americans. Proponents argue forgiveness would unleash economic activity, while critics see it as regressive policy benefiting the already advantaged.",
        "key_points": ["Economic impact", "Fairness", "Moral hazard", "Root causes"],
        "pros": [
            "Stimulates economic growth and mobility",
            "Addresses predatory lending practices",
            "Reduces racial wealth gap disparities",
            "Invests in educated workforce"
        ],
        "cons": [
            "Benefits degree-holders over non-graduates",
            "Creates moral hazard for future borrowing",
            "Doesn't address underlying tuition costs",
            "Taxpayers bear the burden"
        ],
        "fallacies": ["Appeal to emotion", "Slippery slope"],
        "sources": ["Federal Reserve data", "Brookings Institution analysis"]
    },
    {
        "id": "year-round-school",
        "title": "Should schools implement year-round education?",
        "category": "Education",
        "summary": "Rethinking the traditional school calendar to reduce summer learning loss.",
        "description": "Year-round schooling distributes breaks throughout the year instead of one long summer vacation. Advocates cite reduced learning loss, while opponents value summer for enrichment, family time, and teacher development.",
        "key_points": ["Learning retention", "Break distribution", "Family impact", "Facility usage"],
        "pros": [
            "Reduces summer learning loss significantly",
            "Prevents teacher and student burnout",
            "Maximizes school facility investment",
            "Eases childcare burden on families"
        ],
        "cons": [
            "Disrupts summer enrichment opportunities",
            "Creates scheduling challenges for families",
            "Mixed research on academic benefits",
            "Limits teacher professional development time"
        ],
        "fallacies": ["Appeal to tradition", "Cherry picking data"],
        "sources": ["National Association for Year-Round Education", "NAEP data"]
    },
    {
        "id": "phone-ban-schools",
        "title": "Should schools ban mobile phones entirely?",
        "category": "Education",
        "summary": "Addressing smartphone distraction and mental health in educational settings.",
        "description": "Studies show phones reduce cognitive capacity even when not in use. Schools worldwide are implementing bans, but critics argue phones have educational value and bans don't teach self-regulation.",
        "key_points": ["Attention and focus", "Mental health", "Safety", "Digital citizenship"],
        "pros": [
            "Eliminates constant distraction from learning",
            "Reduces cyberbullying and social comparison",
            "Promotes face-to-face social interaction",
            "Easier to enforce than partial restrictions"
        ],
        "cons": [
            "Phones are essential safety communication tools",
            "Misses opportunity to teach digital citizenship",
            "Has legitimate educational applications",
            "Creates adversarial enforcement dynamics"
        ],
        "fallacies": ["False dilemma", "Slippery slope"],
        "sources": ["UNESCO global report", "Common Sense Media research"]
    },
    {
        "id": "ai-tutoring",
        "title": "Should AI tutoring systems replace human tutors?",
        "category": "Technology",
        "summary": "The role of artificial intelligence in personalized education.",
        "description": "AI tutors offer unlimited patience, 24/7 availability, and personalized learning paths. However, they cannot replicate the emotional support, mentorship, and adaptive creativity of human educators.",
        "key_points": ["Personalization", "Availability", "Emotional support", "Cost"],
        "pros": [
            "Provides unlimited patience and availability",
            "Adapts to individual learning pace and style",
            "Dramatically reduces tutoring costs",
            "Removes social barriers to asking questions"
        ],
        "cons": [
            "Cannot provide emotional support and mentorship",
            "Lacks intuition for student frustration",
            "May reinforce misconceptions inappropriately",
            "Reduces human interaction skills development"
        ],
        "fallacies": ["False dilemma", "Appeal to novelty"],
        "sources": ["Stanford HAI reports", "EdTech research journals"]
    },
    {
        "id": "ai-regulation",
        "title": "Should artificial intelligence be heavily regulated?",
        "category": "Technology",
        "summary": "Balancing AI innovation with safety, privacy, and ethical concerns.",
        "description": "AI systems increasingly affect employment, privacy, and decision-making. Proponents of regulation cite risks of bias and job displacement, while critics worry regulation will stifle innovation and cede leadership to less regulated nations.",
        "key_points": ["Safety", "Innovation", "Global competition", "Ethics"],
        "pros": [
            "Prevents algorithmic bias and discrimination",
            "Protects privacy and data rights",
            "Ensures accountability for AI decisions",
            "Addresses job displacement proactively"
        ],
        "cons": [
            "May stifle innovation and competitiveness",
            "Difficult to regulate rapidly evolving technology",
            "Could push development to less regulated countries",
            "One-size-fits-all rules may not work"
        ],
        "fallacies": ["Slippery slope", "Appeal to fear"],
        "sources": ["EU AI Act", "NIST AI Risk Management Framework"]
    },
    {
        "id": "social-media-age",
        "title": "Should there be a minimum age for social media use?",
        "category": "Technology",
        "summary": "Protecting children from social media's effects on mental health and development.",
        "description": "Research links social media use to increased anxiety, depression, and body image issues in young people. Age restrictions aim to protect developing minds, but enforcement challenges and platform incentives complicate implementation.",
        "key_points": ["Mental health", "Age verification", "Parental rights", "Enforcement"],
        "pros": [
            "Protects developing brains from addictive design",
            "Reduces cyberbullying and social comparison harm",
            "Allows time for real-world social development",
            "Addresses documented mental health impacts"
        ],
        "cons": [
            "Age verification is technically difficult",
            "May drive usage to less safe platforms",
            "Restricts parental choice and autonomy",
            "Doesn't address underlying platform design issues"
        ],
        "fallacies": ["Appeal to fear", "Oversimplification"],
        "sources": ["Surgeon General advisory", "Pew Research Center data"]
    },
    {
        "id": "remote-work",
        "title": "Should companies mandate return to office?",
        "category": "Policy",
        "summary": "The future of work: remote flexibility vs in-person collaboration.",
        "description": "The pandemic proved remote work is viable for many roles, but employers increasingly mandate office return citing collaboration and culture. Workers value flexibility, creating tension over the future of work.",
        "key_points": ["Productivity", "Collaboration", "Work-life balance", "Real estate"],
        "pros": [
            "Enhances spontaneous collaboration and mentorship",
            "Builds company culture and team cohesion",
            "Provides clear work-life boundaries",
            "Justifies real estate investments"
        ],
        "cons": [
            "Remote workers often show equal or higher productivity",
            "Commuting wastes time and increases emissions",
            "Flexibility improves employee satisfaction and retention",
            "Enables access to broader talent pools"
        ],
        "fallacies": ["Appeal to tradition", "False dilemma"],
        "sources": ["Stanford remote work studies", "Gallup workplace surveys"]
    },
    {
        "id": "universal-basic-income",
        "title": "Should governments implement universal basic income?",
        "category": "Policy",
        "summary": "Unconditional cash payments as a response to automation and inequality.",
        "description": "UBI proposes regular cash payments to all citizens regardless of employment. Proponents see it as a safety net for automation-driven job losses, while critics worry about costs, inflation, and work incentives.",
        "key_points": ["Poverty reduction", "Automation", "Work incentives", "Funding"],
        "pros": [
            "Provides economic security and reduces poverty",
            "Simplifies complex welfare bureaucracy",
            "Supports unpaid care and creative work",
            "Cushions transition to automated economy"
        ],
        "cons": [
            "Massive funding requirements and tax increases",
            "May reduce work incentives for some",
            "Could cause inflation if not designed carefully",
            "Doesn't address non-monetary needs"
        ],
        "fallacies": ["Appeal to novelty", "Oversimplification"],
        "sources": ["Finland UBI experiment", "GiveDirectly research"]
    },
    {
        "id": "carbon-tax",
        "title": "Should governments implement carbon taxes?",
        "category": "Environment",
        "summary": "Using market mechanisms to reduce greenhouse gas emissions.",
        "description": "Carbon taxes make polluters pay for emissions, incentivizing clean energy adoption. Supporters cite economic efficiency, while opponents worry about impacts on consumers and international competitiveness.",
        "key_points": ["Emissions reduction", "Economic impact", "Revenue use", "Global coordination"],
        "pros": [
            "Creates market incentive to reduce emissions",
            "More efficient than command-and-control regulation",
            "Generates revenue for clean energy investment",
            "Transparent and predictable for business planning"
        ],
        "cons": [
            "Regressive impact on lower-income households",
            "May hurt competitiveness vs non-taxing countries",
            "Political difficulty of implementing new taxes",
            "Uncertain emission reduction effectiveness"
        ],
        "fallacies": ["False dilemma", "Appeal to fear"],
        "sources": ["IMF climate reports", "World Bank carbon pricing data"]
    },
    {
        "id": "nuclear-energy",
        "title": "Should nuclear power be part of the clean energy transition?",
        "category": "Environment",
        "summary": "Nuclear energy as a low-carbon baseload power source.",
        "description": "Nuclear provides reliable, low-carbon electricity but faces concerns about safety, waste, and cost. New technologies promise improvements, but public perception and regulatory hurdles remain challenges.",
        "key_points": ["Carbon emissions", "Safety", "Waste disposal", "Cost"],
        "pros": [
            "Produces zero direct carbon emissions",
            "Provides reliable baseload power",
            "High energy density with small land footprint",
            "New designs offer improved safety features"
        ],
        "cons": [
            "Radioactive waste storage unsolved long-term",
            "High construction costs and delays",
            "Catastrophic accident potential (rare but severe)",
            "Nuclear proliferation concerns"
        ],
        "fallacies": ["Appeal to fear", "Hasty generalization"],
        "sources": ["IPCC reports", "World Nuclear Association data"]
    },
]


def _tokenize(text: str) -> set[str]:
    """Simple tokenization for search."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return set(w for w in text.split() if len(w) > 2)


def search_topics(query: str) -> TopicSearchResponse:
    """
    Search topics using keyword matching.

    Args:
        query: Search query string

    Returns:
        TopicSearchResponse with matching topics
    """
    if not query.strip():
        # Return all topics if empty query
        results = [
            TopicSummary(
                id=t["id"],
                title=t["title"],
                category=t["category"],
                summary=t["summary"]
            )
            for t in TOPICS
        ]
        return TopicSearchResponse(results=results)

    query_tokens = _tokenize(query)
    scored_topics = []

    for topic in TOPICS:
        # Build searchable text
        searchable = " ".join([
            topic["title"],
            topic["category"],
            topic["summary"],
            topic["description"],
            " ".join(topic.get("key_points", [])),
        ])
        topic_tokens = _tokenize(searchable)

        # Score by overlap
        overlap = len(query_tokens & topic_tokens)
        if overlap > 0:
            scored_topics.append((overlap, topic))

    # Sort by score descending
    scored_topics.sort(key=lambda x: x[0], reverse=True)

    results = [
        TopicSummary(
            id=t["id"],
            title=t["title"],
            category=t["category"],
            summary=t["summary"]
        )
        for _, t in scored_topics
    ]

    return TopicSearchResponse(results=results)


def get_topic(topic_id: str) -> TopicDetail | None:
    """
    Get detailed topic information by ID.

    Args:
        topic_id: Topic identifier

    Returns:
        TopicDetail or None if not found
    """
    for topic in TOPICS:
        if topic["id"] == topic_id:
            return TopicDetail(
                id=topic["id"],
                title=topic["title"],
                category=topic["category"],
                summary=topic["summary"],
                description=topic["description"],
                keyPoints=topic.get("key_points", []),
                pros=topic.get("pros", []),
                cons=topic.get("cons", []),
                fallacies=topic.get("fallacies", []),
                sources=topic.get("sources", []),
            )
    return None


def get_topic_by_title(title: str) -> TopicDetail | None:
    """
    Find topic by title (fuzzy match).

    Args:
        title: Topic title to search for

    Returns:
        TopicDetail or None if not found
    """
    title_lower = title.lower()
    for topic in TOPICS:
        if title_lower in topic["title"].lower() or topic["title"].lower() in title_lower:
            return get_topic(topic["id"])
    return None
