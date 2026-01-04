"""
Research Agent - Retrieves relevant passages from local corpus.

Implements a simple BM25-based retrieval for the debate system.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path
from dataclasses import dataclass
from src.agents.base import Agent, AgentState, DebateContext


@dataclass
class Passage:
    """A retrieved passage from the corpus."""
    text: str
    source: str
    score: float
    domain: str


class SimpleBM25:
    """
    Simple BM25 implementation for local retrieval.

    This is a lightweight implementation that doesn't require
    external dependencies like rank_bm25 or elasticsearch.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_freqs = Counter()
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.n_docs = 0
        self.tokenized_docs = []

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return [w for w in text.split() if len(w) > 2]

    def fit(self, documents: list[dict]):
        """Index documents for retrieval."""
        self.documents = documents
        self.n_docs = len(documents)

        for doc in documents:
            tokens = self._tokenize(doc["text"])
            self.tokenized_docs.append(tokens)
            self.doc_lengths.append(len(tokens))
            self.doc_freqs.update(set(tokens))

        self.avg_doc_length = sum(self.doc_lengths) / self.n_docs if self.n_docs > 0 else 0

    def _idf(self, term: str) -> float:
        """Compute IDF for a term."""
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0
        return math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1)

    def _score_document(self, query_tokens: list[str], doc_idx: int) -> float:
        """Score a single document against query."""
        doc_tokens = self.tokenized_docs[doc_idx]
        doc_length = self.doc_lengths[doc_idx]
        doc_term_freqs = Counter(doc_tokens)

        score = 0.0
        for term in query_tokens:
            if term in doc_term_freqs:
                tf = doc_term_freqs[term]
                idf = self._idf(term)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                score += idf * numerator / denominator

        return score

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """
        Search for documents matching query.

        Returns:
            List of (doc_index, score) tuples
        """
        query_tokens = self._tokenize(query)
        scores = []

        for i in range(self.n_docs):
            score = self._score_document(query_tokens, i)
            if score > 0:
                scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# Sample corpus for the education domain
# In production, this would be loaded from data/corpus/
SAMPLE_CORPUS = {
    "education": [
        {
            "text": "Standardized testing has been shown to provide reliable metrics for comparing student achievement across different schools and districts. However, critics argue that these tests narrow the curriculum and create undue stress.",
            "source": "education_policy_review_2023.txt"
        },
        {
            "text": "Research on homework effectiveness shows mixed results. For elementary students, homework has minimal impact on achievement, while for high school students, moderate amounts correlate with improved performance.",
            "source": "homework_meta_analysis.txt"
        },
        {
            "text": "Online education enrollment increased by 300% during the pandemic, forcing universities to rapidly develop digital learning infrastructure. Studies show that while flexible, online learning requires greater self-motivation.",
            "source": "online_education_trends.txt"
        },
        {
            "text": "Computer science education has become increasingly important in K-12 curricula. Countries like Estonia and Singapore have mandated coding from early grades, with positive results in logical thinking skills.",
            "source": "cs_education_global_report.txt"
        },
        {
            "text": "Teacher evaluation systems based primarily on student test scores have faced criticism for failing to account for socioeconomic factors and prior student preparation levels.",
            "source": "teacher_evaluation_study.txt"
        },
        {
            "text": "Student loan debt in the United States has surpassed $1.7 trillion, with average borrowers owing over $30,000. This debt burden affects major life decisions including homeownership and family formation.",
            "source": "student_debt_analysis.txt"
        },
        {
            "text": "Year-round schooling schedules typically involve 45 days of instruction followed by 15-day breaks. Proponents argue this reduces summer learning loss, particularly for disadvantaged students.",
            "source": "calendar_reform_handbook.txt"
        },
        {
            "text": "Mobile phone policies in schools vary widely. France banned phones for students under 15 in 2018, while other countries promote BYOD (bring your own device) policies for educational use.",
            "source": "technology_policy_comparison.txt"
        },
        {
            "text": "Affirmative action in university admissions aims to increase diversity and correct historical inequities. The Supreme Court has placed limits on race-conscious admissions in recent decisions.",
            "source": "admissions_policy_law_review.txt"
        },
        {
            "text": "AI tutoring systems can provide immediate feedback and adapt to individual learning speeds. However, they cannot replace the emotional support and mentorship that human teachers provide.",
            "source": "ai_education_review.txt"
        },
    ],
}


class ResearchAgent(Agent):
    """
    Retrieves relevant passages from a local corpus.

    Uses BM25 for efficient keyword-based retrieval.
    """

    def __init__(self, corpus_dir: Path | None = None):
        super().__init__("Research")
        self.corpus_dir = corpus_dir
        self.indexes = {}  # domain -> BM25 index
        self._load_corpus()

    def _load_corpus(self):
        """Load corpus and build indexes."""
        # Use sample corpus for now
        # In production, load from self.corpus_dir
        for domain, documents in SAMPLE_CORPUS.items():
            index = SimpleBM25()
            index.fit(documents)
            self.indexes[domain] = (index, documents)

    def retrieve(
        self,
        query: str,
        domain: str,
        top_k: int = 3,
    ) -> list[Passage]:
        """
        Retrieve relevant passages for a query.

        Args:
            query: Search query
            domain: Domain to search in
            top_k: Number of passages to retrieve

        Returns:
            List of Passage objects
        """
        if domain not in self.indexes:
            # Fall back to education domain
            domain = "education"

        index, documents = self.indexes[domain]
        results = index.search(query, top_k=top_k)

        passages = []
        for doc_idx, score in results:
            doc = documents[doc_idx]
            passages.append(Passage(
                text=doc["text"],
                source=doc["source"],
                score=score,
                domain=domain,
            ))

        return passages

    def process(self, context: DebateContext) -> DebateContext:
        """Retrieve relevant passages for the debate topic."""
        self._log(context, "starting_research", {
            "topic": context.topic,
            "domain": context.domain,
        })

        # Retrieve passages
        passages = self.retrieve(
            query=context.topic,
            domain=context.domain or "education",
            top_k=5,
        )

        context.retrieved_passages = [
            {
                "text": p.text,
                "source": p.source,
                "score": p.score,
                "domain": p.domain,
            }
            for p in passages
        ]

        context.corpus_stats = {
            "num_retrieved": len(passages),
            "avg_score": sum(p.score for p in passages) / len(passages) if passages else 0,
            "sources": list(set(p.source for p in passages)),
        }

        self._log(context, "research_complete", {
            "num_passages": len(passages),
            "top_score": passages[0].score if passages else 0,
        })

        context.current_state = AgentState.DEBATING_PRO
        return context
