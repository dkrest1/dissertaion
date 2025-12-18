import os
import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta


def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


# Load .env for local convenience
_load_dotenv()

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    # fallback to github_token.txt for backwards compatibility
    try:
        TOKEN = open("github_token.txt").read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            "GitHub token not found. Set the GITHUB_TOKEN environment variable or create a local github_token.txt (do NOT commit it)."
        )

HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

# Allow using an external file with repo list (one per line) named repos.txt
if os.path.exists("repos.txt"):
    with open("repos.txt") as f:
        repos = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
else:
    repos = [
            "pytorch/pytorch",
            "tensorflow/tensorflow",
            "apache/spark",
            "kubernetes/kubernetes",
            "nodejs/node",
            "facebook/react",
            "golang/go",
            "rust-lang/rust",
            "microsoft/vscode",
            "huggingface/transformers",
        ]

all_runs = []

# Allow user to set a MAX_RUNS via environment (defaults to 1500). This limits
# the total number of runs collected across all repos to keep collection bounded.
MAX_RUNS = int(os.environ.get("MAX_RUNS", "2000"))
# Optionally only collect runs created within the last N days (default 90).
# This increases the chance that logs are still available when downloading.
CREATED_AFTER_DAYS = int(os.environ.get("CREATED_AFTER_DAYS", "90"))
# Use naive UTC cutoff for comparison by converting parsed datetimes to UTC naive.
created_after_cutoff = (datetime.utcnow() - timedelta(days=CREATED_AFTER_DAYS)).replace(tzinfo=None)

for repo in repos:
    if len(all_runs) >= MAX_RUNS:
        break
    print(f"Fetching workflow runs for {repo}... (collected so far: {len(all_runs)})")
    # Request only completed runs (avoids in-progress runs which often have no logs yet)
    url = f"https://api.github.com/repos/{repo}/actions/runs?conclusion=failure&status=completed&per_page=100"

    while url and len(all_runs) < MAX_RUNS:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()

        if "workflow_runs" not in data:
            break

        for run in data["workflow_runs"]:
            # Filter by creation date if available
            created_at_str = run.get("created_at")
            try:
                # parse ISO timestamp and convert to naive UTC
                created_at = None
                if created_at_str:
                    created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    # convert to UTC naive
                    created_at = created_at_dt.astimezone(tz=None).replace(tzinfo=None)
            except Exception:
                created_at = None

            if created_at and created_at < created_after_cutoff:
                # skip older runs
                continue

            all_runs.append({
                "repo": repo,
                "run_id": run["id"],
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "created_at": run.get("created_at"),
                "log_url": run.get("logs_url"),
            })
            if len(all_runs) >= MAX_RUNS:
                break

        # Pagination - extract next page from Link header
        link = r.headers.get("Link", "")
        next_url = None
        if link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip()[1:-1]
                    break
        url = next_url

df = pd.DataFrame(all_runs)
df.to_csv("workflow_runs.csv", index=False)
print(f"Saved workflow_runs.csv ({len(all_runs)} runs)")
