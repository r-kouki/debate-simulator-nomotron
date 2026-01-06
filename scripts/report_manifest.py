from __future__ import annotations

import json
import os
import sys
from pathlib import Path

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
    now_utc,
    read_json,
    sha256_file,
    write_json,
)


REPORT_LOG = LOG_DIR / "report.log"


def collect_jsonl_counts(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in iter_jsonl(path))


def collect_token_estimate(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        for record in iter_jsonl(path):
            total += estimate_tokens(record.get("text", ""))
    return total


def update_checksums(paths: list[Path]) -> None:
    checksums_path = MANIFEST_DIR / "checksums.json"
    payload = read_json(checksums_path) or {"files": {}, "generated_at": now_utc()}
    files = payload.get("files", {})
    for path in paths:
        if not path.exists():
            continue
        rel = str(path.relative_to(SCRIPT_DIR.parents[1]))
        files[rel] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "timestamp_utc": now_utc(),
        }
    payload["files"] = files
    payload["generated_at"] = now_utc()
    write_json(checksums_path, payload)


def write_readme() -> None:
    readme_path = MANIFEST_DIR / "README.md"
    content = "\n".join(
        [
            "# Data Manifests",
            "",
            "This folder tracks dataset provenance, licenses, versions, and checksums.",
            "",
            "- `sources.json`: source catalog with URLs, local paths, and domains.",
            "- `licenses.json`: license or usage notes per source.",
            "- `versions.json`: dataset revisions, git commits, and scrape logs.",
            "- `checksums.json`: sha256 hashes for downloaded and generated files.",
            "- `DATA_REPORT.md`: summary counts, splits, and exclusions.",
            "",
            "Stack Exchange dumps are excluded from training unless explicitly approved.",
        ]
    )
    readme_path.write_text(content, encoding="utf-8")


def write_data_report(stats: dict) -> None:
    report_path = MANIFEST_DIR / "DATA_REPORT.md"
    sources = stats.get("sources", [])
    licenses = stats.get("licenses", {})
    split_sizes = stats.get("split_sizes", {})
    corpus_stats = stats.get("corpus_stats", {})
    sft_counts = stats.get("sft_counts", {})

    lines = ["# Data Report", "", "## Sources"]
    for source in sorted(sources, key=lambda s: s.get("source_id", "")):
        lines.append(
            f"- {source.get('source_id')}: {source.get('url')} (domain: {source.get('domain')})"
        )

    lines.append("")
    lines.append("## Licenses")
    for source_id, license_name in sorted(licenses.items()):
        lines.append(f"- {source_id}: {license_name}")

    lines.append("")
    lines.append("## Corpus Counts")
    lines.append("| domain | documents | token_estimate | sft_examples |")
    lines.append("| --- | ---: | ---: | ---: |")
    for domain in sorted(corpus_stats.keys()):
        domain_stats = corpus_stats[domain]
        lines.append(
            f"| {domain} | {domain_stats.get('documents', 0)} | "
            f"{domain_stats.get('token_estimate', 0)} | {sft_counts.get(domain, 0)} |"
        )

    lines.append("")
    lines.append("## Split Sizes")
    lines.append("| domain | train | val | test |")
    lines.append("| --- | ---: | ---: | ---: |")
    for domain in sorted(split_sizes.keys()):
        sizes = split_sizes[domain]
        lines.append(
            f"| {domain} | {sizes.get('train', 0)} | {sizes.get('val', 0)} | {sizes.get('test', 0)} |"
        )

    lines.append("")
    lines.append("## Exclusions")
    lines.append(
        "- Stack Exchange dumps are not used for training unless explicitly approved."
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dir(LOG_DIR)
    ensure_dir(MANIFEST_DIR)

    sources_payload = read_json(MANIFEST_DIR / "sources.json")
    licenses_payload = read_json(MANIFEST_DIR / "licenses.json")
    corpus_stats_payload = read_json(MANIFEST_DIR / "corpus_stats.json")

    sources = sources_payload.get("sources", [])
    licenses = licenses_payload.get("licenses", {})
    corpus_stats = corpus_stats_payload.get("domains", {})

    sft_counts = {}
    for path in SFT_DIR.glob("*.jsonl"):
        sft_counts[path.stem] = collect_jsonl_counts(path)

    split_sizes = {}
    for domain_dir in SPLITS_DIR.iterdir():
        if not domain_dir.is_dir():
            continue
        split_sizes[domain_dir.name] = {
            "train": collect_jsonl_counts(domain_dir / "train.jsonl"),
            "val": collect_jsonl_counts(domain_dir / "val.jsonl"),
            "test": collect_jsonl_counts(domain_dir / "test.jsonl"),
        }

    if not corpus_stats:
        corpus_stats = {}
        for path in CORPUS_DIR.glob("*.jsonl"):
            domain = path.stem.replace("_web", "")
            corpus_stats.setdefault(domain, {"documents": 0, "token_estimate": 0})
            corpus_stats[domain]["documents"] += collect_jsonl_counts(path)
            corpus_stats[domain]["token_estimate"] += collect_token_estimate([path])

    stats = {
        "sources": sources,
        "licenses": licenses,
        "corpus_stats": corpus_stats,
        "sft_counts": sft_counts,
        "split_sizes": split_sizes,
    }

    manifest_paths = list(CORPUS_DIR.glob("*.jsonl")) + list(SFT_DIR.glob("*.jsonl"))
    for domain_dir in SPLITS_DIR.iterdir():
        if domain_dir.is_dir():
            manifest_paths.extend(domain_dir.glob("*.jsonl"))
    update_checksums(manifest_paths)

    if os.environ.get("CHECK_RAW") == "1":
        raw_paths = [path for path in RAW_DIR.rglob("*") if path.is_file()]
        update_checksums(raw_paths)

    write_readme()
    write_data_report(stats)

    append_log(REPORT_LOG, "manifest report generated")


if __name__ == "__main__":
    main()
