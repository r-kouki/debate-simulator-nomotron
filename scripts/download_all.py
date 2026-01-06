from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import requests
from huggingface_hub import HfApi, snapshot_download

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_pipeline_utils import (  # noqa: E402
    LOG_DIR,
    MANIFEST_DIR,
    RAW_DIR,
    append_log,
    ensure_dir,
    init_manifest,
    now_utc,
    sha256_file,
    update_manifest,
)


DOWNLOAD_LOG = LOG_DIR / "download.log"
HF_API = HfApi()


def normalize_key(value: str) -> str:
    return value.strip().lower()


def parse_filter(name: str) -> set[str]:
    raw = os.environ.get(name, "")
    if not raw:
        return set()
    return {normalize_key(item) for item in raw.split(",") if item.strip()}


DOWNLOAD_ONLY = parse_filter("DOWNLOAD_ONLY")
DOWNLOAD_SKIP = parse_filter("DOWNLOAD_SKIP")


def is_selected(*keys: Optional[str]) -> bool:
    normalized = [normalize_key(key) for key in keys if key]
    if DOWNLOAD_SKIP and any(key in DOWNLOAD_SKIP for key in normalized):
        return False
    if not DOWNLOAD_ONLY:
        return True
    return any(key in DOWNLOAD_ONLY for key in normalized)


def is_offline() -> bool:
    return any(
        os.environ.get(key) == "1"
        for key in ["OFFLINE", "HF_HUB_OFFLINE", "HF_DATASETS_OFFLINE", "TRANSFORMERS_OFFLINE"]
    )


def init_manifests() -> None:
    init_manifest(MANIFEST_DIR / "sources.json", {"generated_at": now_utc(), "sources": []})
    init_manifest(MANIFEST_DIR / "licenses.json", {"generated_at": now_utc(), "licenses": {}})
    init_manifest(MANIFEST_DIR / "versions.json", {"generated_at": now_utc(), "sources": {}})
    init_manifest(MANIFEST_DIR / "checksums.json", {"generated_at": now_utc(), "files": {}})


def record_source(entry: dict) -> None:
    def updater(payload: dict) -> dict:
        sources = payload.get("sources", [])
        sources = [s for s in sources if s.get("source_id") != entry.get("source_id")]
        sources.append(entry)
        payload["sources"] = sources
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "sources.json", updater)


def record_license(source_id: str, license_name: str) -> None:
    def updater(payload: dict) -> dict:
        licenses = payload.get("licenses", {})
        if license_name != "unknown" or source_id not in licenses:
            licenses[source_id] = license_name
        payload["licenses"] = licenses
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "licenses.json", updater)


def record_version(source_id: str, version_payload: dict) -> None:
    def updater(payload: dict) -> dict:
        sources = payload.get("sources", {})
        existing = sources.get(source_id, {})
        merged = {**existing}
        for key, value in version_payload.items():
            if value is not None:
                merged[key] = value
        sources[source_id] = merged
        payload["sources"] = sources
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "versions.json", updater)


def iter_checksum_files(local_dir: Path):
    for path in local_dir.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.name in {".download_complete", ".checksums_complete"}:
            continue
        yield path


def record_checksums_for_dir(local_dir: Path, source_id: str) -> None:
    sentinel = local_dir / ".checksums_complete"
    if sentinel.exists():
        append_log(DOWNLOAD_LOG, f"skip checksums {source_id}: already computed")
        return
    files = list(iter_checksum_files(local_dir))
    if not files:
        append_log(DOWNLOAD_LOG, f"no files for checksum {source_id}")
        return

    def updater(payload: dict) -> dict:
        entries = payload.get("files", {})
        for path in files:
            try:
                rel = str(path.relative_to(SCRIPT_DIR.parents[1]))
            except ValueError:
                rel = str(path)
            entries[rel] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "timestamp_utc": now_utc(),
            }
        payload["files"] = entries
        payload["generated_at"] = now_utc()
        return payload

    update_manifest(MANIFEST_DIR / "checksums.json", updater)
    sentinel.write_text(now_utc(), encoding="utf-8")


def run_hf_download(repo_id: str, local_dir: Path, revision: Optional[str] = None) -> None:
    use_cli = os.environ.get("HF_USE_CLI") == "1"
    if use_cli and shutil.which("hf"):
        cmd = [
            "hf",
            "download",
            repo_id,
            "--repo-type",
            "dataset",
            "--local-dir",
            str(local_dir),
            "--local-dir-use-symlinks",
            "False",
        ]
        if revision:
            cmd.extend(["--revision", revision])
        append_log(DOWNLOAD_LOG, f"hf cli download: {' '.join(cmd)}")
        subprocess.check_call(cmd)
    else:
        append_log(DOWNLOAD_LOG, f"snapshot_download: {repo_id} -> {local_dir}")
        try:
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
                revision=revision,
            )
        except Exception as exc:
            message = str(exc)
            if "xet" in message.lower() or "cas service error" in message.lower():
                append_log(DOWNLOAD_LOG, f"retry without xet for {repo_id}: {message}")
                os.environ["HF_HUB_DISABLE_XET"] = "1"
                snapshot_download(
                    repo_id=repo_id,
                    repo_type="dataset",
                    local_dir=str(local_dir),
                    local_dir_use_symlinks=False,
                    revision=revision,
                )
            else:
                raise


def download_hf_dataset(
    repo_id: str,
    local_dir: Path,
    domain: str,
    alias: Optional[str] = None,
    revision: Optional[str] = None,
) -> None:
    ensure_dir(local_dir)
    sentinel = local_dir / ".download_complete"
    downloaded = False
    source_id = repo_id
    if sentinel.exists():
        append_log(DOWNLOAD_LOG, f"skip {repo_id}: already downloaded")
    else:
        if is_offline():
            raise RuntimeError(f"OFFLINE=1 but dataset missing: {repo_id}")
        run_hf_download(repo_id, local_dir, revision=revision)
        sentinel.write_text(now_utc(), encoding="utf-8")
        downloaded = True

    info = None
    license_name = "unknown"
    if not is_offline():
        try:
            info = HF_API.dataset_info(repo_id, revision=revision)
            if info and info.cardData:
                license_name = info.cardData.get("license", license_name)
        except Exception as exc:
            append_log(DOWNLOAD_LOG, f"dataset_info failed for {repo_id}: {exc}")

    record_source(
        {
            "source_id": source_id,
            "alias": alias or source_id,
            "type": "hf_dataset",
            "domain": domain,
            "url": f"https://huggingface.co/datasets/{repo_id}",
            "local_path": str(local_dir.relative_to(SCRIPT_DIR.parents[1])),
        }
    )
    record_license(source_id, license_name)
    version_payload = {
        "timestamp_utc": now_utc(),
        "hf_revision": revision or "main",
        "hf_sha": getattr(info, "sha", None),
    }
    if downloaded or info is not None:
        record_version(source_id, version_payload)
    record_checksums_for_dir(local_dir, source_id)


def git_clone(repo_url: str, local_dir: Path, source_id: str, domain: str) -> None:
    ensure_dir(local_dir.parent)
    if local_dir.exists():
        append_log(DOWNLOAD_LOG, f"skip {source_id}: repo exists at {local_dir}")
    else:
        if is_offline():
            raise RuntimeError(f"OFFLINE=1 but repo missing: {source_id}")
        append_log(DOWNLOAD_LOG, f"git clone {repo_url} -> {local_dir}")
        subprocess.check_call(["git", "clone", repo_url, str(local_dir)])
    commit = None
    try:
        commit = (
            subprocess.check_output(["git", "-C", str(local_dir), "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except Exception as exc:
        append_log(DOWNLOAD_LOG, f"git rev-parse failed for {source_id}: {exc}")
    record_source(
        {
            "source_id": source_id,
            "type": "github_repo",
            "domain": domain,
            "url": repo_url,
            "local_path": str(local_dir.relative_to(SCRIPT_DIR.parents[1])),
        }
    )
    record_license(source_id, "unknown")
    record_version(source_id, {"timestamp_utc": now_utc(), "git_commit": commit})
    record_checksums_for_dir(local_dir, source_id)


def extract_drive_file_ids(folder_html: str) -> dict:
    ids = {}
    for match in re.finditer(r'"([^"]+)\.json","([^"]+)"', folder_html):
        name = match.group(1) + ".json"
        file_id = match.group(2)
        ids[name] = file_id
    if ids:
        return ids
    for match in re.finditer(r'"(debates\.json|users\.json)".*?"id":"([^"]+)"', folder_html):
        ids[match.group(1)] = match.group(2)
    return ids


def extract_drive_id(value: str) -> Optional[str]:
    match = re.search(r"(?:id=|/d/|folders/)([a-zA-Z0-9_-]{10,})", value)
    if match:
        return match.group(1)
    return None


def download_gdrive_file(file_id: str, dest_path: Path) -> None:
    ensure_dir(dest_path.parent)
    url = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={"id": file_id}, stream=True, timeout=60)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
    if token:
        response = session.get(url, params={"id": file_id, "confirm": token}, stream=True, timeout=60)
    response.raise_for_status()
    with dest_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)


def download_ddo(local_dir: Path) -> None:
    ensure_dir(local_dir)
    sentinel = local_dir / ".download_complete"
    debates_path = local_dir / "debates.json"
    users_path = local_dir / "users.json"
    if debates_path.exists() and users_path.exists():
        append_log(DOWNLOAD_LOG, "skip DDO: already downloaded")
        if not sentinel.exists():
            sentinel.write_text(now_utc(), encoding="utf-8")
        record_source(
            {
                "source_id": "DDO",
                "type": "gdrive_folder",
                "domain": "debate",
                "url": "https://esdurmus.github.io/ddo.html",
                "local_path": str(local_dir.relative_to(SCRIPT_DIR.parents[1])),
                "notes": "Google Drive folder download; store debates.json and users.json",
            }
        )
        record_license("DDO", "unknown")
        record_version(
            "DDO",
            {
                "timestamp_utc": now_utc(),
                "gdrive_folder_id": os.environ.get("DDO_GDRIVE_FOLDER_ID"),
                "files": ["debates.json", "users.json"],
            },
        )
        record_checksums_for_dir(local_dir, "DDO")
        return

    ddo_page = "https://esdurmus.github.io/ddo.html"
    folder_id = os.environ.get("DDO_GDRIVE_FOLDER_ID")
    folder_url = os.environ.get("DDO_GDRIVE_FOLDER_URL")
    if folder_url and not folder_id:
        folder_id = extract_drive_id(folder_url)
    file_ids: dict[str, str] = {}
    if is_offline():
        raise RuntimeError("OFFLINE=1 but DDO files are missing")
    debates_url = os.environ.get("DDO_DEBATES_URL")
    users_url = os.environ.get("DDO_USERS_URL")
    if debates_url:
        resolved = extract_drive_id(debates_url)
        if resolved:
            file_ids["debates.json"] = resolved
    if users_url:
        resolved = extract_drive_id(users_url)
        if resolved:
            file_ids["users.json"] = resolved
    manual_debates = os.environ.get("DDO_DEBATES_FILE_ID")
    manual_users = os.environ.get("DDO_USERS_FILE_ID")
    if manual_debates:
        file_ids["debates.json"] = manual_debates
    if manual_users:
        file_ids["users.json"] = manual_users
    if file_ids.get("debates.json") and file_ids.get("users.json"):
        append_log(DOWNLOAD_LOG, "DDO file IDs provided via env")
    if not folder_id:
        append_log(DOWNLOAD_LOG, f"fetch DDO page: {ddo_page}")
        response = requests.get(ddo_page, timeout=30)
        response.raise_for_status()
        match = re.search(r"drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)", response.text)
        if match:
            folder_id = match.group(1)
    if folder_id:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        append_log(DOWNLOAD_LOG, f"fetch DDO folder page: {folder_url}")
        html = requests.get(folder_url, timeout=30).text
        file_ids.update(extract_drive_file_ids(html))

    if not file_ids:
        raise RuntimeError(
            "Unable to resolve DDO file IDs. Set DDO_GDRIVE_FOLDER_ID/URL or "
            "DDO_DEBATES_FILE_ID/DDO_USERS_FILE_ID or DDO_DEBATES_URL/DDO_USERS_URL env vars."
        )

    for filename, file_id in file_ids.items():
        dest = local_dir / filename
        if dest.exists():
            append_log(DOWNLOAD_LOG, f"skip DDO file {filename}: exists")
            continue
        append_log(DOWNLOAD_LOG, f"download DDO file {filename} (id={file_id})")
        download_gdrive_file(file_id, dest)
    sentinel.write_text(now_utc(), encoding="utf-8")

    record_source(
        {
            "source_id": "DDO",
            "type": "gdrive_folder",
            "domain": "debate",
            "url": ddo_page,
            "local_path": str(local_dir.relative_to(SCRIPT_DIR.parents[1])),
            "notes": "Google Drive folder download; store debates.json and users.json",
        }
    )
    record_license("DDO", "unknown")
    record_version(
        "DDO",
        {
            "timestamp_utc": now_utc(),
            "gdrive_folder_id": folder_id,
            "files": sorted(file_ids.keys()),
        },
    )
    record_checksums_for_dir(local_dir, "DDO")


def main() -> None:
    ensure_dir(RAW_DIR)
    ensure_dir(LOG_DIR)
    ensure_dir(MANIFEST_DIR)
    init_manifests()

    hf_datasets = []
    if os.environ.get("DOWNLOAD_OPENCASLIST") == "1":
        hf_datasets.append(
            {
                "repo_id": "Yusuf5/OpenCaselist",
                "local_dir": RAW_DIR / "OpenDebateEvidence",
                "domain": "debate",
                "alias": "OpenDebateEvidence",
            }
        )
    else:
        append_log(
            DOWNLOAD_LOG,
            "skip Yusuf5/OpenCaselist (set DOWNLOAD_OPENCASLIST=1 to download)",
        )

    hf_datasets.extend(
        [
            {
                "repo_id": "Hellisotherpeople/DebateSum",
                "local_dir": RAW_DIR / "DebateSum",
                "domain": "debate",
                "alias": "DebateSum",
            },
            {
                "repo_id": "openlifescienceai/medmcqa",
                "local_dir": RAW_DIR / "medmcqa",
                "domain": "medicine",
                "alias": "medmcqa",
            },
            {
                "repo_id": "bigbio/pubmed_qa",
                "local_dir": RAW_DIR / "pubmed_qa",
                "domain": "medicine",
                "alias": "pubmed_qa",
            },
            {
                "repo_id": "crumb/openstax-text",
                "local_dir": RAW_DIR / "openstax",
                "domain": "education",
                "alias": "openstax",
            },
            {
                "repo_id": "tdiggelm/climate_fever",
                "local_dir": RAW_DIR / "climate_fever",
                "domain": "ecology",
                "alias": "climate_fever",
            },
        ]
    )

    for dataset in hf_datasets:
        repo_id = dataset["repo_id"]
        alias = dataset.get("alias")
        if not is_selected(repo_id, alias):
            append_log(DOWNLOAD_LOG, f"skip {repo_id}: not selected (DOWNLOAD_ONLY)")
            continue
        download_hf_dataset(**dataset)

    med_collection = os.environ.get(
        "MEDICAL_QA_DATASETS",
        "lavita/MedQuAD,medalpaca/medical_meadow_medical_qa,medalpaca/medical_meadow_medical_flashcards,medalpaca/medical_meadow_wikidoc",
    )
    med_collection_dir = RAW_DIR / "medical_qa_collection"
    for repo_id in [name.strip() for name in med_collection.split(",") if name.strip()]:
        safe_name = repo_id.replace("/", "__")
        alias = f"medical_qa_collection/{safe_name}"
        if not is_selected(repo_id, safe_name, alias, "medical_qa_collection"):
            append_log(DOWNLOAD_LOG, f"skip {repo_id}: not selected (DOWNLOAD_ONLY)")
            continue
        download_hf_dataset(
            repo_id=repo_id,
            local_dir=med_collection_dir / safe_name,
            domain="medicine",
            alias=alias,
        )

    medquad_repo = os.environ.get("MEDQUAD_REPO", "https://github.com/abachaa/MedQuAD")
    iam_repo = os.environ.get("IAM_REPO", "https://github.com/LiyingCheng95/IAM")
    if is_selected("MedQuAD", medquad_repo):
        git_clone(medquad_repo, RAW_DIR / "MedQuAD", "MedQuAD", "medicine")
    else:
        append_log(DOWNLOAD_LOG, "skip MedQuAD: not selected (DOWNLOAD_ONLY)")
    if is_selected("IAM", iam_repo):
        git_clone(iam_repo, RAW_DIR / "IAM", "IAM", "debate")
    else:
        append_log(DOWNLOAD_LOG, "skip IAM: not selected (DOWNLOAD_ONLY)")

    if is_selected("DDO"):
        download_ddo(RAW_DIR / "DDO")
    else:
        append_log(DOWNLOAD_LOG, "skip DDO: not selected (DOWNLOAD_ONLY)")

    if os.environ.get("DOWNLOAD_THE_STACK") == "1" and is_selected("bigcode/the-stack-dedup", "the_stack_dedup"):
        download_hf_dataset(
            repo_id="bigcode/the-stack-dedup",
            local_dir=RAW_DIR / "the_stack_dedup",
            domain="technology",
            alias="the_stack_dedup",
        )
        record_source(
            {
                "source_id": "bigcode/the-stack-dedup",
                "type": "hf_dataset",
                "domain": "technology",
                "url": "https://huggingface.co/datasets/bigcode/the-stack-dedup",
                "local_path": "data/raw/the_stack_dedup",
                "notes": "NOT FOR TRAINING unless explicitly approved.",
            }
        )
        record_license("bigcode/the-stack-dedup", "assorted (see dataset card)")
    elif os.environ.get("DOWNLOAD_THE_STACK") == "1":
        append_log(DOWNLOAD_LOG, "skip bigcode/the-stack-dedup: not selected (DOWNLOAD_ONLY)")


if __name__ == "__main__":
    main()
