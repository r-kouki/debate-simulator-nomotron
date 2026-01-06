from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_pipeline_utils import (  # noqa: E402
    CORPUS_DIR,
    LOG_DIR,
    MANIFEST_DIR,
    append_log,
    ensure_dir,
    init_manifest,
    now_utc,
    sleep_with_jitter,
    stable_hash,
    truncate_text,
    update_manifest,
    write_jsonl,
)


SCRAPE_LOG = LOG_DIR / "scrape.log"
USER_AGENT = "debate-simulator/1.0 (+local academic project)"


def can_fetch(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return False, robots_url
    return parser.can_fetch(USER_AGENT, url), robots_url


def record_scrape_version(source_id: str, url: str, robots_allowed: bool, robots_url: str) -> None:
    def updater(payload: dict) -> dict:
        sources = payload.get("sources", {})
        source_payload = sources.get(source_id, {})
        history = source_payload.get("scrapes", [])
        history.append(
            {
                "url": url,
                "robots_allowed": robots_allowed,
                "robots_url": robots_url,
                "timestamp_utc": now_utc(),
            }
        )
        source_payload["scrapes"] = history
        sources[source_id] = source_payload
        payload["sources"] = sources
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "versions.json", updater)


def record_source(source_id: str, domain: str, base_url: str) -> None:
    def updater(payload: dict) -> dict:
        sources = payload.get("sources", [])
        sources = [s for s in sources if s.get("source_id") != source_id]
        sources.append(
            {
                "source_id": source_id,
                "type": "web",
                "domain": domain,
                "url": base_url,
                "local_path": f"data/corpus/{domain}_web.jsonl",
            }
        )
        payload["sources"] = sources
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "sources.json", updater)


def record_license(source_id: str, license_name: str) -> None:
    def updater(payload: dict) -> dict:
        licenses = payload.get("licenses", {})
        licenses[source_id] = license_name
        payload["licenses"] = licenses
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "licenses.json", updater)


def fetch_and_extract(url: str) -> tuple[str | None, dict]:
    downloaded = trafilatura.fetch_url(url, user_agent=USER_AGENT)
    if not downloaded:
        return None, {}
    metadata = trafilatura.metadata.extract_metadata(downloaded)
    text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
    meta_payload = {}
    if metadata:
        meta_payload = {
            "title": metadata.title,
            "author": metadata.author,
            "date": metadata.date,
            "description": metadata.description,
            "site_name": metadata.sitename,
            "url": metadata.url,
        }
    return text, meta_payload


def scrape_domain(domain: str, urls: list[str], output_path: Path, source_id: str, license_name: str) -> None:
    ensure_dir(output_path.parent)
    base_url = urls[0] if urls else f"https://{source_id}"
    record_source(source_id, domain, base_url)
    record_license(source_id, license_name)
    for url in urls:
        robots_allowed, robots_url = can_fetch(url)
        record_scrape_version(source_id, url, robots_allowed, robots_url)
        if not robots_allowed:
            append_log(SCRAPE_LOG, f"robots disallow {url}")
            sleep_with_jitter(1.0)
            continue
        append_log(SCRAPE_LOG, f"scrape {url}")
        text, metadata = fetch_and_extract(url)
        if not text:
            append_log(SCRAPE_LOG, f"no text extracted {url}")
            sleep_with_jitter(1.0)
            continue
        doc = {
            "domain": domain,
            "source": "web",
            "source_id": source_id,
            "source_url": url,
            "license": license_name,
            "doc_id": stable_hash(f"{source_id}:{url}"),
            "title": metadata.get("title") if metadata else None,
            "text": truncate_text(text, max_chars=8000),
            "metadata": metadata,
            "timestamp_utc": now_utc(),
        }
        write_jsonl(output_path, [doc])
        append_log(SCRAPE_LOG, f"saved {url}")
        sleep_with_jitter(1.0)


def main() -> None:
    ensure_dir(LOG_DIR)
    ensure_dir(CORPUS_DIR)
    ensure_dir(MANIFEST_DIR)
    init_manifest(MANIFEST_DIR / "sources.json", {"generated_at": now_utc(), "sources": []})
    init_manifest(MANIFEST_DIR / "licenses.json", {"generated_at": now_utc(), "licenses": {}})
    init_manifest(MANIFEST_DIR / "versions.json", {"generated_at": now_utc(), "sources": {}})
    if os.environ.get("ENABLE_SCRAPE") != "1":
        append_log(SCRAPE_LOG, "scrape_optional skipped (ENABLE_SCRAPE != 1)")
        return

    scrape_targets = [
        {
            "domain": "medicine",
            "source_id": "who.int",
            "license": "see site terms",
            "urls": [
                "https://www.who.int/health-topics/antimicrobial-resistance",
                "https://www.who.int/news-room/fact-sheets/detail/antibiotic-resistance",
            ],
        },
        {
            "domain": "medicine",
            "source_id": "cdc.gov",
            "license": "see site terms",
            "urls": [
                "https://www.cdc.gov/antibiotic-use/community/about/antibiotic-resistance-faqs.html",
            ],
        },
        {
            "domain": "ecology",
            "source_id": "ipcc.ch",
            "license": "see site terms",
            "urls": [
                "https://www.ipcc.ch/report/ar6/wg1/",
                "https://www.ipcc.ch/report/ar6/wg2/",
            ],
        },
        {
            "domain": "education",
            "source_id": "openstax.org",
            "license": "cc-by-4.0 (see OpenStax)",
            "urls": [
                "https://openstax.org/subjects",
                "https://openstax.org/details/books/psychology-2e",
            ],
        },
        {
            "domain": "technology",
            "source_id": "oecd.ai",
            "license": "see site terms",
            "urls": [
                "https://oecd.ai/en/ai-principles",
                "https://oecd.ai/en/dashboards",
            ],
        },
    ]

    for payload in scrape_targets:
        output_path = CORPUS_DIR / f"{payload['domain']}_web.jsonl"
        scrape_domain(
            domain=payload["domain"],
            urls=payload["urls"],
            output_path=output_path,
            source_id=payload["source_id"],
            license_name=payload["license"],
        )


if __name__ == "__main__":
    main()
