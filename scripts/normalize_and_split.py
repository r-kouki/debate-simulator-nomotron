from __future__ import annotations

import json
import os
import random
import sys
import csv
import pyarrow.parquet as pq
from itertools import chain
from pathlib import Path
from typing import Iterable, Iterator

from datasets import load_dataset

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_pipeline_utils import (  # noqa: E402
    CORPUS_DIR,
    LOG_DIR,
    MANIFEST_DIR,
    RAW_DIR,
    SFT_DIR,
    SPLITS_DIR,
    append_log,
    ensure_dir,
    estimate_tokens,
    iter_jsonl,
    load_text_file,
    now_utc,
    stable_hash,
    truncate_text,
    write_json,
    write_jsonl,
)


NORMALIZE_LOG = LOG_DIR / "normalize.log"
SEED = 42
MAX_DOCS_PER_SOURCE = int(os.environ.get("MAX_DOCS_PER_SOURCE", "0") or 0)
MAX_SFT_PER_DOMAIN = int(os.environ.get("MAX_SFT_PER_DOMAIN", "0") or 0)


def limit_records(records: Iterable[dict], limit: int, label: str) -> Iterator[dict]:
    if not limit or limit <= 0:
        yield from records
        return
    count = 0
    for record in records:
        if count >= limit:
            append_log(NORMALIZE_LOG, f"{label}: reached limit {limit}")
            break
        yield record
        count += 1


def get_license_map() -> dict:
    path = MANIFEST_DIR / "licenses.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data.get("licenses", {})
    return {}


def to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    return str(value).strip()


def first_field(record: dict, keys: list[str]) -> str:
    for key in keys:
        if key in record and record[key]:
            return to_text(record[key])
    return ""


def make_doc(
    domain: str,
    source: str,
    source_id: str,
    license_name: str,
    text: str,
    source_url: str | None = None,
    title: str | None = None,
    metadata: dict | None = None,
    doc_id: str | None = None,
) -> dict | None:
    if not text or not text.strip():
        return None
    safe_text = text.strip()
    if not doc_id:
        doc_id = stable_hash(f"{source_id}:{title or ''}:{safe_text[:500]}")
    return {
        "domain": domain,
        "source": source,
        "source_id": source_id,
        "source_url": source_url,
        "license": license_name,
        "doc_id": doc_id,
        "title": title,
        "text": safe_text,
        "metadata": metadata or {},
        "timestamp_utc": now_utc(),
    }


def iter_hf_dataset(repo_id: str, local_dir: Path) -> Iterator[tuple[dict, str]]:
    dataset = None
    offline = os.environ.get("OFFLINE") == "1" or os.environ.get("HF_DATASETS_OFFLINE") == "1"
    try:
        dataset = load_dataset(
            str(local_dir),
            streaming=True,
            local_files_only=offline,
        )
    except Exception as exc:
        append_log(NORMALIZE_LOG, f"load_dataset local failed {repo_id}: {exc}")
    if dataset is None and local_dir.exists():
        data_files = []
        for ext in ["*.jsonl", "*.json", "*.csv", "*.parquet", "*.txt"]:
            data_files.extend(local_dir.rglob(ext))
        if data_files:
            for record in iter_local_records(data_files):
                yield record, "train"
            return
    if dataset is None and not offline:
        try:
            dataset = load_dataset(repo_id, streaming=True)
        except Exception as exc:
            append_log(NORMALIZE_LOG, f"load_dataset remote failed {repo_id}: {exc}")
            if os.environ.get("ALLOW_MISSING_DATA") == "1":
                return
            raise
    if dataset is None and offline:
        if os.environ.get("ALLOW_MISSING_DATA") == "1":
            return
        raise RuntimeError(f"Dataset unavailable offline: {repo_id}")
    if hasattr(dataset, "items"):
        for split_name, split_data in dataset.items():
            for record in split_data:
                yield record, split_name
    else:
        for record in dataset:
            yield record, "train"


def iter_local_records(data_files: list[Path]) -> Iterator[dict]:
    for path in sorted(data_files):
        if path.suffix == ".csv":
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    yield dict(row)
        elif path.suffix == ".jsonl":
            for record in iter_jsonl(path):
                yield record
        elif path.suffix == ".json":
            for record in iter_json_records(path):
                yield record
        elif path.suffix == ".parquet":
            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(batch_size=2048):
                for record in batch.to_pylist():
                    yield record
        elif path.suffix == ".txt":
            text = load_text_file(path)
            if text.strip():
                yield {"title": path.stem, "text": truncate_text(text, max_chars=20000)}


def normalize_opencaselist(records: Iterable[tuple[dict, str]], license_name: str) -> Iterator[dict]:
    source_id = "Yusuf5/OpenCaselist"
    source_url = f"https://huggingface.co/datasets/{source_id}"
    for record, split in records:
        topic = first_field(record, ["topic", "title", "motion", "claim"])
        stance = first_field(record, ["stance", "position", "side"])
        argument = first_field(record, ["argument", "argument_text", "claim", "text", "content"])
        evidence = first_field(record, ["evidence", "premise", "context", "support"])
        text = "\n".join(part for part in [argument, evidence] if part)
        metadata = {
            "topic": topic or None,
            "stance": stance or None,
            "split": split,
        }
        doc = make_doc(
            domain="debate",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=topic or None,
            metadata=metadata,
            doc_id=record.get("id") or record.get("uid"),
        )
        if doc:
            yield doc


def normalize_debatesum(records: Iterable[tuple[dict, str]], license_name: str) -> Iterator[dict]:
    source_id = "Hellisotherpeople/DebateSum"
    source_url = f"https://huggingface.co/datasets/{source_id}"
    for record, split in records:
        topic = first_field(record, ["Tag", "topic", "title", "question", "OriginalDebateFileName"])
        extract = first_field(record, ["Extract", "extract", "excerpt"])
        summary = first_field(record, ["Abstract", "summary"])
        citation = first_field(record, ["Citation", "citation"])
        text = "\n".join(part for part in [extract, summary, citation] if part)
        metadata = {
            "topic": topic or None,
            "citation": citation or None,
            "camp": record.get("DebateCamp"),
            "tag": record.get("Tag"),
            "year": record.get("Year"),
            "split": split,
        }
        doc = make_doc(
            domain="debate",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=topic or None,
            metadata=metadata,
            doc_id=record.get("id"),
        )
        if doc:
            yield doc


def normalize_medmcqa(records: Iterable[tuple[dict, str]], license_name: str) -> Iterator[dict]:
    source_id = "openlifescienceai/medmcqa"
    source_url = f"https://huggingface.co/datasets/{source_id}"
    for record, split in records:
        question = first_field(record, ["question", "query"])
        options = []
        for key in ["opa", "opb", "opc", "opd", "option_a", "option_b", "option_c", "option_d"]:
            if record.get(key):
                options.append(record[key])
        answer = record.get("answer") or record.get("cop")
        explanation = record.get("exp") or record.get("explanation")
        option_block = "\n".join(f"- {to_text(opt)}" for opt in options if opt)
        text = "\n".join(part for part in [question, option_block, f"Answer: {answer}", explanation] if part)
        metadata = {
            "question": question or None,
            "answer": to_text(answer) if answer else None,
            "options": [to_text(opt) for opt in options if opt],
            "split": split,
        }
        doc = make_doc(
            domain="medicine",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=None,
            metadata=metadata,
            doc_id=record.get("id"),
        )
        if doc:
            yield doc


def normalize_pubmed_qa(records: Iterable[tuple[dict, str]], license_name: str) -> Iterator[dict]:
    source_id = "bigbio/pubmed_qa"
    source_url = f"https://huggingface.co/datasets/{source_id}"
    for record, split in records:
        question = first_field(record, ["question", "query"])
        context = first_field(record, ["context", "abstract", "article", "long_context"])
        answer = first_field(record, ["long_answer", "final_decision", "answer"])
        text = "\n".join(part for part in [question, context, answer] if part)
        metadata = {
            "question": question or None,
            "answer": answer or None,
            "label": record.get("final_decision"),
            "split": split,
        }
        doc = make_doc(
            domain="medicine",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=None,
            metadata=metadata,
            doc_id=record.get("id") or record.get("pubid"),
        )
        if doc:
            yield doc


def normalize_openstax(records: Iterable[tuple[dict, str]], license_name: str) -> Iterator[dict]:
    source_id = "crumb/openstax-text"
    source_url = f"https://huggingface.co/datasets/{source_id}"
    for record, split in records:
        title = first_field(record, ["title", "chapter", "section", "book"])
        text = first_field(record, ["text", "content", "body"])
        metadata = {
            "title": title or None,
            "book": record.get("book"),
            "chapter": record.get("chapter"),
            "section": record.get("section"),
            "split": split,
        }
        doc = make_doc(
            domain="education",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=title or None,
            metadata=metadata,
            doc_id=record.get("id"),
        )
        if doc:
            yield doc


def normalize_climate_fever(records: Iterable[tuple[dict, str]], license_name: str) -> Iterator[dict]:
    source_id = "tdiggelm/climate_fever"
    source_url = f"https://huggingface.co/datasets/{source_id}"
    for record, split in records:
        claim = first_field(record, ["claim", "statement", "question"])
        evidence = first_field(record, ["evidence", "context", "article"])
        label = record.get("label") or record.get("verdict")
        text = "\n".join(part for part in [claim, evidence] if part)
        metadata = {"label": label, "topic": claim or None, "split": split}
        doc = make_doc(
            domain="ecology",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=claim or None,
            metadata=metadata,
            doc_id=record.get("id"),
        )
        if doc:
            yield doc


def normalize_medical_collection(
    repo_id: str, records: Iterable[tuple[dict, str]], license_name: str
) -> Iterator[dict]:
    source_id = repo_id
    source_url = f"https://huggingface.co/datasets/{repo_id}"
    for record, split in records:
        instruction = first_field(record, ["instruction", "prompt", "question"])
        answer = first_field(record, ["output", "answer", "response"])
        context = first_field(record, ["context", "input"])
        text = "\n".join(part for part in [instruction, context, answer] if part)
        metadata = {
            "question": instruction or None,
            "answer": answer or None,
            "split": split,
        }
        doc = make_doc(
            domain="medicine",
            source="hf",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=instruction or None,
            metadata=metadata,
            doc_id=record.get("id"),
        )
        if doc:
            yield doc


def iter_json_records(path: Path) -> Iterator[dict]:
    if path.suffix == ".jsonl":
        yield from iter_jsonl(path)
        return
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        for record in payload:
            yield record
    elif isinstance(payload, dict):
        records = payload.get("data") or payload.get("records") or payload.get("items")
        if isinstance(records, list):
            for record in records:
                yield record


def normalize_iam(license_name: str) -> Iterator[dict]:
    source_id = "IAM"
    source_url = "https://github.com/LiyingCheng95/IAM"
    iam_dir = RAW_DIR / "IAM"
    json_paths = list(iam_dir.rglob("*.json")) + list(iam_dir.rglob("*.jsonl"))
    if not json_paths:
        append_log(NORMALIZE_LOG, "IAM: no json/jsonl files found")
        return
    for path in json_paths:
        for record in iter_json_records(path):
            topic = first_field(record, ["topic", "title", "question"])
            claim = first_field(record, ["claim", "argument", "argument_text", "text"])
            evidence = first_field(record, ["evidence", "premise", "support", "context"])
            stance = first_field(record, ["stance", "position", "label"])
            text = "\n".join(part for part in [claim, evidence] if part)
            metadata = {
                "topic": topic or None,
                "stance": stance or None,
                "claim": claim or None,
                "evidence": evidence or None,
            }
            doc = make_doc(
                domain="debate",
                source="github",
                source_id=source_id,
                license_name=license_name,
                text=text,
                source_url=source_url,
                title=topic or None,
                metadata=metadata,
            )
            if doc:
                yield doc


def normalize_medquad(license_name: str) -> Iterator[dict]:
    source_id = "MedQuAD"
    source_url = "https://github.com/abachaa/MedQuAD"
    medquad_dir = RAW_DIR / "MedQuAD"
    xml_paths = list(medquad_dir.rglob("*.xml"))
    if not xml_paths:
        append_log(NORMALIZE_LOG, "MedQuAD: no xml files found")
        return
    for path in xml_paths:
        try:
            from xml.etree import ElementTree

            tree = ElementTree.parse(path)
            root = tree.getroot()
        except Exception as exc:
            append_log(NORMALIZE_LOG, f"MedQuAD xml parse failed {path}: {exc}")
            continue
        for qa in root.findall(".//QAPair"):
            question = to_text(qa.findtext("Question"))
            answer = to_text(qa.findtext("Answer"))
            text = "\n".join(part for part in [question, answer] if part)
            metadata = {"question": question or None, "answer": answer or None}
            doc = make_doc(
                domain="medicine",
                source="github",
                source_id=source_id,
                license_name=license_name,
                text=text,
                source_url=source_url,
                title=question or None,
                metadata=metadata,
            )
            if doc:
                yield doc


def normalize_ddo(license_name: str) -> Iterator[dict]:
    source_id = "DDO"
    source_url = "https://esdurmus.github.io/ddo.html"
    ddo_dir = RAW_DIR / "DDO"
    debates_path = ddo_dir / "debates.json"
    if not debates_path.exists():
        append_log(NORMALIZE_LOG, "DDO: debates.json missing")
        return
    with debates_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    debates = payload.get("debates") if isinstance(payload, dict) else payload
    if not isinstance(debates, list):
        append_log(NORMALIZE_LOG, "DDO: debates.json format unexpected")
        return
    for debate in debates:
        title = first_field(debate, ["title", "topic", "question"])
        pro = first_field(debate, ["pro", "pro_text", "argument_pro"])
        con = first_field(debate, ["con", "con_text", "argument_con"])
        text = "\n".join(part for part in [title, f"Pro: {pro}", f"Con: {con}"] if part)
        metadata = {
            "topic": title or None,
            "pro": pro or None,
            "con": con or None,
            "category": debate.get("category"),
        }
        doc = make_doc(
            domain="debate",
            source="gdrive",
            source_id=source_id,
            license_name=license_name,
            text=text,
            source_url=source_url,
            title=title or None,
            metadata=metadata,
            doc_id=debate.get("id"),
        )
        if doc:
            yield doc


def reset_file(path: Path) -> None:
    if path.exists():
        path.unlink()


def write_domain_corpus(domain: str, records: Iterable[dict]) -> Path:
    output_path = CORPUS_DIR / f"{domain}.jsonl"
    reset_file(output_path)
    count = 0
    for record in records:
        write_jsonl(output_path, [record])
        count += 1
        if count % 5000 == 0:
            append_log(NORMALIZE_LOG, f"{domain}: wrote {count} records")
    if count == 0:
        output_path.write_text("", encoding="utf-8")
    append_log(NORMALIZE_LOG, f"{domain}: wrote {count} records total")
    return output_path


def build_sft_examples(domain: str, corpus_paths: list[Path]) -> Path:
    output_path = SFT_DIR / f"{domain}.jsonl"
    reset_file(output_path)
    rng = random.Random(SEED)
    count = 0
    reached_limit = False
    for path in corpus_paths:
        for doc in iter_jsonl(path):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {}) or {}
            title = doc.get("title") or metadata.get("topic")
            context = truncate_text(text, max_chars=1200)
            examples = []
            if metadata.get("question") and metadata.get("answer"):
                question = metadata["question"]
                answer = metadata["answer"]
                examples.append(
                    {
                        "text": f"<|user|>\nAnswer the question based on the context.\n"
                        f"Question: {question}\nContext: {context}\n<|assistant|>\n{answer}"
                    }
                )
            if title and context:
                response = context.split(". ")[0].strip()
                examples.append(
                    {
                        "text": f"<|user|>\nExplain the concept \"{title}\" using the context.\n"
                        f"Context: {context}\n<|assistant|>\n{response}"
                    }
                )
            stance = metadata.get("stance") or rng.choice(["pro", "con"])
            if context:
                response = context.split(". ")[0].strip()
                examples.append(
                    {
                        "text": f"<|user|>\nWrite a {stance} debate turn grounded in the context.\n"
                        f"Context: {context}\n<|assistant|>\n{response}"
                    }
                )
            if metadata.get("claim") or metadata.get("evidence"):
                claim = metadata.get("claim") or ""
                evidence = metadata.get("evidence") or ""
                examples.append(
                    {
                        "text": "<|user|>\nExtract the claim and evidence from the context.\n"
                        f"Context: {context}\n<|assistant|>\nClaim: {claim}\nEvidence: {evidence}"
                    }
                )
            for example in examples[:3]:
                write_jsonl(output_path, [example])
                count += 1
                if MAX_SFT_PER_DOMAIN and count >= MAX_SFT_PER_DOMAIN:
                    append_log(
                        NORMALIZE_LOG,
                        f"{domain}: reached SFT limit {MAX_SFT_PER_DOMAIN}",
                    )
                    reached_limit = True
                    break
            if reached_limit:
                break
        if reached_limit:
            break
    append_log(NORMALIZE_LOG, f"{domain}: wrote {count} SFT examples")
    return output_path


def split_for_domain(domain: str, corpus_paths: list[Path]) -> None:
    domain_dir = SPLITS_DIR / domain
    ensure_dir(domain_dir)
    train_path = domain_dir / "train.jsonl"
    val_path = domain_dir / "val.jsonl"
    test_path = domain_dir / "test.jsonl"
    reset_file(train_path)
    reset_file(val_path)
    reset_file(test_path)

    def assign_split(doc: dict) -> str:
        metadata = doc.get("metadata", {}) or {}
        topic = metadata.get("topic") or doc.get("title") or doc.get("source_id")
        key = f"{SEED}:{topic}:{doc.get('doc_id')}"
        bucket = int(stable_hash(key), 16) % 100
        if bucket < 80:
            return "train"
        if bucket < 90:
            return "val"
        return "test"

    counts = {"train": 0, "val": 0, "test": 0}
    for path in corpus_paths:
        for doc in iter_jsonl(path):
            split = assign_split(doc)
            if split == "train":
                write_jsonl(train_path, [doc])
            elif split == "val":
                write_jsonl(val_path, [doc])
            else:
                write_jsonl(test_path, [doc])
            counts[split] += 1
    append_log(NORMALIZE_LOG, f"{domain}: split counts {counts}")


def main() -> None:
    ensure_dir(LOG_DIR)
    ensure_dir(CORPUS_DIR)
    ensure_dir(SFT_DIR)
    ensure_dir(SPLITS_DIR)

    license_map = get_license_map()

    debate_records = chain(
        normalize_opencaselist(
            limit_records(
                iter_hf_dataset("Yusuf5/OpenCaselist", RAW_DIR / "OpenDebateEvidence"),
                MAX_DOCS_PER_SOURCE,
                "OpenCaselist",
            ),
            license_map.get("Yusuf5/OpenCaselist", "unknown"),
        ),
        normalize_debatesum(
            limit_records(
                iter_hf_dataset("Hellisotherpeople/DebateSum", RAW_DIR / "DebateSum"),
                MAX_DOCS_PER_SOURCE,
                "DebateSum",
            ),
            license_map.get("Hellisotherpeople/DebateSum", "unknown"),
        ),
        limit_records(
            normalize_iam(license_map.get("IAM", "unknown")),
            MAX_DOCS_PER_SOURCE,
            "IAM",
        ),
        limit_records(
            normalize_ddo(license_map.get("DDO", "unknown")),
            MAX_DOCS_PER_SOURCE,
            "DDO",
        ),
    )
    debate_corpus = write_domain_corpus("debate", debate_records)

    med_collection_dir = RAW_DIR / "medical_qa_collection"
    med_collection_records = []
    if med_collection_dir.exists():
        for dataset_dir in med_collection_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
            repo_id = dataset_dir.name.replace("__", "/")
            med_collection_records.append(
                normalize_medical_collection(
                    repo_id,
                    limit_records(
                        iter_hf_dataset(repo_id, dataset_dir),
                        MAX_DOCS_PER_SOURCE,
                        repo_id,
                    ),
                    license_map.get(repo_id, "unknown"),
                )
            )
    medicine_records = chain(
        normalize_medmcqa(
            limit_records(
                iter_hf_dataset("openlifescienceai/medmcqa", RAW_DIR / "medmcqa"),
                MAX_DOCS_PER_SOURCE,
                "medmcqa",
            ),
            license_map.get("openlifescienceai/medmcqa", "unknown"),
        ),
        normalize_pubmed_qa(
            limit_records(
                iter_hf_dataset("bigbio/pubmed_qa", RAW_DIR / "pubmed_qa"),
                MAX_DOCS_PER_SOURCE,
                "pubmed_qa",
            ),
            license_map.get("bigbio/pubmed_qa", "unknown"),
        ),
        limit_records(
            normalize_medquad(license_map.get("MedQuAD", "unknown")),
            MAX_DOCS_PER_SOURCE,
            "MedQuAD",
        ),
        *med_collection_records,
    )
    medicine_corpus = write_domain_corpus("medicine", medicine_records)

    education_records = normalize_openstax(
        limit_records(
            iter_hf_dataset("crumb/openstax-text", RAW_DIR / "openstax"),
            MAX_DOCS_PER_SOURCE,
            "openstax",
        ),
        license_map.get("crumb/openstax-text", "unknown"),
    )
    education_corpus = write_domain_corpus("education", education_records)

    ecology_records = normalize_climate_fever(
        limit_records(
            iter_hf_dataset("tdiggelm/climate_fever", RAW_DIR / "climate_fever"),
            MAX_DOCS_PER_SOURCE,
            "climate_fever",
        ),
        license_map.get("tdiggelm/climate_fever", "unknown"),
    )
    ecology_corpus = write_domain_corpus("ecology", ecology_records)

    technology_corpus = None
    tech_docs = []
    if (RAW_DIR / "the_stack_dedup").exists():
        append_log(NORMALIZE_LOG, "the_stack_dedup present but not normalized by default")
    if tech_docs:
        technology_corpus = write_domain_corpus("technology", tech_docs)

    domain_files = {
        "debate": [debate_corpus],
        "medicine": [medicine_corpus],
        "education": [education_corpus],
        "ecology": [ecology_corpus],
    }
    if technology_corpus:
        domain_files["technology"] = [technology_corpus]

    for domain in list(domain_files.keys()):
        web_path = CORPUS_DIR / f"{domain}_web.jsonl"
        if web_path.exists():
            domain_files[domain].append(web_path)

    sft_outputs = {}
    for domain, files in domain_files.items():
        sft_outputs[domain] = build_sft_examples(domain, files)
        split_for_domain(domain, files)

    stats = {}
    for domain, files in domain_files.items():
        total_docs = sum(1 for path in files for _ in iter_jsonl(path))
        total_tokens = sum(estimate_tokens(doc.get("text", "")) for path in files for doc in iter_jsonl(path))
        stats[domain] = {"documents": total_docs, "token_estimate": total_tokens}
    write_json(MANIFEST_DIR / "corpus_stats.json", {"generated_at": now_utc(), "domains": stats})


if __name__ == "__main__":
    main()
