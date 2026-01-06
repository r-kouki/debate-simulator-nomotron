# Data Manifests

This folder records dataset provenance, licenses, versions, and checksums for the
debate simulator data pipeline. Run `python scripts/pipeline.py` to populate and
refresh the files below.

- `sources.json`: source catalog with URLs, local paths, and domains.
- `licenses.json`: license or usage notes per source.
- `versions.json`: dataset revisions, git commits, and scrape logs.
- `checksums.json`: sha256 hashes for downloaded and generated files.
- `DATA_REPORT.md`: summary counts, splits, and exclusions.
