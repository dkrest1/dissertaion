# Explainable Anomaly Detection in GitHub Actions Build Logs (Memory Log Failure) Using Isolation Forest

This repository contains scripts and utilities to collect GitHub Actions workflow run logs, extract and filter logs from failed builds, and prepare data for anomaly detection (planned using an Isolation Forest model). The goal is to detect and explain anomalous build failures — especially memory-related failures — to support an MRes dissertation project.

## Table of contents
- Project overview
- Quick start
- Scripts (what each does)
- Configuration & secrets (safe handling)
- Folder layout
- Troubleshooting
- Next steps & research directions

## Project overview
This project collects build logs from GitHub Actions for selected repositories, downloads and extracts logs for failed workflow runs, filters logs for memory-related issues (OOM, killed, exit code 137, etc.), and prepares data for anomaly detection and explainability analysis. The intended anomaly detection approach is to use an Isolation Forest and provide explanations for flagged anomalies.

## Quick start
1. Create and activate a Python virtual environment and install dependencies (already used packages in this repo are `requests`, `pandas`, and `tqdm`):

```bash
cd /home/oluwatosinakande/Downloads/code/dissertaion
source .venv/bin/activate
pip install requests pandas tqdm
```

2. Provide your GitHub token securely (recommended: environment variable):

```bash
# temporary for this shell session
export GITHUB_TOKEN="ghp_xxx..."

# or create a local .env from the included example and load it
cp .env.example .env
# edit .env and set GITHUB_TOKEN=...
set -o allexport; source .env; set +o allexport
```

3. Run the pipeline in order:

```bash
# Fetch failed workflow runs (creates workflow_runs.csv)
python3 get_data.py

# Download logs for those runs (extracts into logs_failure/)
python3 download.py

# Filter extracted logs for memory-related issues
python3 filter_momory_logs.py
```

## What each script does
- `get_data.py` — Queries the GitHub Actions API for workflow runs. It now requests only runs with `conclusion=failure` and writes `workflow_runs.csv` with metadata (repo, run_id, log_url, etc.).
- `download.py` — Reads `workflow_runs.csv`, downloads the ZIP logs from GitHub for each run, and extracts them into `logs_failure/` (failed runs) or `logs_normal/` (successful runs, optional).
- `filter_momory_logs.py` — Walks the extracted logs and looks for memory-related keywords (`137`, `killed`, `oom`, `out of memory`, `memory limit`, etc.). It writes matched file paths to `memory_logs.txt`.

## Configuration & safe secret handling
- Preferred: set your token in the `GITHUB_TOKEN` environment variable.
- Local fallback: you may create `github_token.txt` locally for convenience, but make sure it is listed in `.gitignore` and never commit it.
- The repo includes `.env.example` showing how to store a token locally; copy it to `.env` and fill the value. Do NOT commit `.env`.
- If you ever accidentally commit a token, revoke it immediately on GitHub (Settings → Developer settings → Personal access tokens) and generate a new one.

## Using token securely in GitHub Actions
1. In your GitHub repository, go to Settings → Secrets → Actions and add a secret named e.g. `GITHUB_TOKEN` (or another name).
2. In your workflow YAML file, pass it to the job as an environment variable:

```yaml
jobs:
  collect-logs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run log collection
        env:
          GITHUB_TOKEN: ${{ secrets.YOUR_SECRET_NAME }}
        run: |
          python3 get_data.py
```

## Folder layout
- `get_data.py` — fetches run metadata
- `download.py` — downloads and extracts logs
- `filter_momory_logs.py` — searches logs for OOM-related keywords
- `workflow_runs.csv` — produced by `get_data.py`
- `logs_failure/` — extracted logs for failed runs (primary data)
- `logs_normal/` — extracted logs for successful runs (optional)
- `memory_logs.txt` — list of file paths that matched memory-related keywords
- `.env.example` — example env file (do not commit your actual `.env`)
- `.gitignore` — ignores secrets and virtual env

## Security notes
- Do NOT commit `github_token.txt`, `.env`, or any file containing secrets.
- If a token was ever committed and pushed, revoke it on GitHub and regenerate a new token.
- To stop tracking a sensitive file but keep it locally:

```bash
git rm --cached github_token.txt
git commit -m "Remove local token file from repository"
git push
```

If the token was committed previously and needs removing from history, you can use dedicated tools (BFG repo-cleaner) or `git filter-branch`. Ask me if you want exact commands for your situation.

## Troubleshooting
- If `get_data.py` raises a token error: ensure `GITHUB_TOKEN` is exported or `github_token.txt` exists locally.
- If pagination seems incomplete: scripts parse GitHub Link header for next page. Ensure network requests succeed and your token has API quota.
- If downloads fail: check that the `log_url` in `workflow_runs.csv` is valid and the token has access to the repository's actions logs.

## Next steps & research directions
1. Data preparation: parse extracted logs into structured features (length, error keywords, timestamps, step durations, resource usage indicators).
2. Anomaly detection: train an Isolation Forest on features derived from the logs to find unusual build runs.
3. Explainability: use model-agnostic tools (SHAP or feature importances) to explain which features led to anomalies.
4. Evaluation: label a subset of runs (OOM, test flakiness, infra errors) to measure precision/recall.
5. Automation: create a GitHub Action to run the data collection regularly and flag anomalies as issues.

## References & notes
- Isolation Forest (Liu et al.) is an unsupervised method that isolates anomalies using random partitions.
- Explainable methods like SHAP can help map feature contributions back to log text and steps.

## Contact / author
This repository supports an MRes dissertation. If you'd like help extending the pipeline (feature extraction, Isolation Forest training, explainability integration, tests), tell me which part to implement next and I can add code and tests.

---
Last updated: December 8, 2025
# dissertaion
mres dissertation