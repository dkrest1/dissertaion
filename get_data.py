import requests
import pandas as pd
from tqdm import tqdm

TOKEN = open("github_token.txt").read().strip()
HEADERS = {"Authorization": f"token {TOKEN}"}

repos = [
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "apache/spark"
]

all_runs = []

for repo in repos:
    print(f"Fetching workflow runs for {repo}...")
    url = f"https://api.github.com/repos/{repo}/actions/runs"

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

        # Pagination
        url = data.get("next")

df = pd.DataFrame(all_runs)
df.to_csv("workflow_runs.csv", index=False)
print("Saved workflow_runs.csv")
