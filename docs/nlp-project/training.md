# Training Notes (Adapters + Data Prep)

This file captures what was done, the logic behind it, and the exact steps used so far.

## Goal
- Train domain QLoRA adapters using existing local datasets only.
- Keep datasets smaller/controlled; scale up only if metrics are weak.
- Save metrics and reports per domain for professor evaluation.

## Changes Made

### 1) Data download controls
File: `scripts/download_all.py`
- Added offline-safe behavior and checksum recording for raw datasets.
- Added selection filters:
  - `DOWNLOAD_ONLY`: comma-separated list of datasets to download.
  - `DOWNLOAD_SKIP`: comma-separated list to skip.
- OpenCaselist made optional by default; requires `DOWNLOAD_OPENCASLIST=1`.
- DDO download can now accept share URLs:
  - `DDO_DEBATES_URL` and `DDO_USERS_URL`.
  - `DDO_GDRIVE_FOLDER_URL` if you want to pass a folder URL.

### 2) Data normalization limits + offline safety
File: `scripts/normalize_and_split.py`
- Added `MAX_DOCS_PER_SOURCE` to cap records per dataset source.
- Added `MAX_SFT_PER_DOMAIN` to cap total SFT examples per domain.
- Added offline mode support:
  - `OFFLINE=1`, `HF_DATASETS_OFFLINE=1`, `HF_HUB_OFFLINE=1`.
  - `ALLOW_MISSING_DATA=1` to skip missing sources.
- Added fallback parsing for local files (CSV/JSON/JSONL/TXT/Parquet) without HF network calls.
- Added TXT handling for OpenStax local books.
- Fixed DebateSum field mapping to use CSV column names.
- Ensured empty corpus files are still created if a domain has zero records.

### 3) SFT dataset support + generic adapter trainer
Files:
- `src/train/dataset.py`
  - Added `load_sft_jsonl` and `prepare_sft_dataset_for_training` for SFT text-only datasets.
- `scripts/train_domain_adapter.py`
  - New generic trainer that loads `data/sft/<domain>.jsonl`.
  - Splits train/val/test by stable hash (seed=42).
  - Saves training report with train/val/test losses + perplexities.
- `src/train/trainer.py`
  - `save_training_report` now accepts `test_loss` and `dataset_sizes`.
  - `get_training_arguments` now accepts dataloader settings to avoid multiprocessing perms issues.

## Data Preparation Steps (Executed)

Command used (offline local processing, capped size):
```
source .venv/bin/activate
OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 ALLOW_MISSING_DATA=1 \
MAX_DOCS_PER_SOURCE=3000 MAX_SFT_PER_DOMAIN=10000 \
python scripts/normalize_and_split.py
```

Results:
- `data/corpus/debate.jsonl` ~3000 records
- `data/corpus/medicine.jsonl` ~6000 records
- `data/corpus/ecology.jsonl` ~1535 records
- `data/corpus/education.jsonl` ~76 records (OpenStax local TXT parsing)
- `data/sft/` generated for all domains:
  - debate: ~6000
  - medicine: 10000 (capped)
  - ecology: ~3070
  - education: 152

## Adapter Training Steps (Executed)

### Education adapter (completed)
Command:
```
source .venv/bin/activate
python scripts/train_domain_adapter.py education
```

Result:
- Adapter saved to: `models/adapters/education`
- Run artifacts: `runs/train/education/20260105_204418`
- Final metrics (from console):
  - Train loss: 1.9324 (PPL 6.91)
  - Val loss: 1.2256 (PPL 3.41)
  - Test loss: 1.3113 (PPL 3.71)

### Ecology adapter (attempted, aborted)
Command:
```
source .venv/bin/activate
TOKENIZERS_PARALLELISM=false python scripts/train_domain_adapter.py ecology
```
Issue:
- First run fell back to CPU due to CUDA initialization errors (Error 304, NVML).
- After verifying GPU with `scripts/verify_base_model.py`, rerun was aborted by user.

## GPU Verification (Executed)
Command:
```
source .venv/bin/activate
python scripts/verify_base_model.py
```
Result:
- CUDA available: True
- GPU: RTX 3090
- Model loaded on `cuda:0`
- Inference success

## Next Recommended Steps

1) Resume training adapters for:
   - `ecology`, `medicine`, `debate`

2) Use GPU and avoid multiprocessing issues:
```
source .venv/bin/activate
TOKENIZERS_PARALLELISM=false python scripts/train_domain_adapter.py ecology
TOKENIZERS_PARALLELISM=false python scripts/train_domain_adapter.py medicine
TOKENIZERS_PARALLELISM=false python scripts/train_domain_adapter.py debate
```

3) If any domain metrics are weak, incrementally raise caps:
```
MAX_DOCS_PER_SOURCE=5000 MAX_SFT_PER_DOMAIN=20000 python scripts/normalize_and_split.py
```

## Notes
- OpenCaselist is huge; only include it if necessary.
- DDO download requires file IDs or share URLs.
- No commands were run outside the repo.
