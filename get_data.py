import os
import requests
import pandas as pd
from tqdm import tqdm

# Read GitHub token from environment variable first (recommended for safety).
# For local convenience you can place the token in a file named `github_token.txt`
# but make sure that file is added to .gitignore so it won't be committed.
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    # fallback to local file for backwards compatibility / local dev
    try:
        TOKEN = open("github_token.txt").read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            "GitHub token not found. Set the GITHUB_TOKEN environment variable or create a local github_token.txt (do NOT commit it)."
        )

HEADERS = {"Authorization": f"token {TOKEN}"}

repos = [
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "apache/spark"
]

all_runs = []

for repo in repos:
    print(f"Fetching workflow runs for {repo}...")
    # Only fetch FAILED runs (conclusion=failure)
    url = f"https://api.github.com/repos/{repo}/actions/runs?conclusion=failure"

    while url:
        r = requests.get(url, headers=HEADERS)
        data = r.json()

        if "workflow_runs" not in data:
            break

        for run in data["workflow_runs"]:
            all_runs.append({
                "repo": repo,
                "run_id": run["id"],
                "status": run["status"],
                "conclusion": run["conclusion"],
                "created_at": run["created_at"],
                "log_url": run["logs_url"]
            })

        # Pagination - extract next page from Link header
        link = r.headers.get("Link", "")
        url = None
        if link:
            # Parse the Link header for 'next' URL
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip()[1:-1]  # Extract URL from <url>
                    break

df = pd.DataFrame(all_runs)
df.to_csv("workflow_runs.csv", index=False)
print("Saved workflow_runs.csv")
