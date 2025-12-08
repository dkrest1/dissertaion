import os
import requests
import pandas as pd
from tqdm import tqdm


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
    ]

all_runs = []

for repo in repos:
    print(f"Fetching workflow runs for {repo}...")
    url = f"https://api.github.com/repos/{repo}/actions/runs?conclusion=failure"

    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()

        if "workflow_runs" not in data:
            break

        for run in data["workflow_runs"]:
            all_runs.append({
                "repo": repo,
                "run_id": run["id"],
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "created_at": run.get("created_at"),
                "log_url": run.get("logs_url"),
            })

        # Pagination - extract next page from Link header
        link = r.headers.get("Link", "")
        url = None
        if link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip()[1:-1]
                    break

df = pd.DataFrame(all_runs)
df.to_csv("workflow_runs.csv", index=False)
print("Saved workflow_runs.csv")
