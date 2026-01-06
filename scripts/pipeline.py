from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]


def run_step(script_name: str) -> None:
    script_path = SCRIPT_DIR / script_name
    subprocess.check_call([sys.executable, str(script_path)])


def main() -> None:
    os.chdir(ROOT)
    run_step("download_all.py")
    run_step("scrape_optional.py")
    run_step("normalize_and_split.py")
    run_step("report_manifest.py")


if __name__ == "__main__":
    main()
