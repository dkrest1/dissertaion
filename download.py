import os
import requests
import pandas as pd
from tqdm import tqdm
import zipfile
import io

# Use environment variable first to avoid leaking tokens in git.
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    try:
        TOKEN = open("github_token.txt").read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            "GitHub token not found. Set the GITHUB_TOKEN environment variable or create a local github_token.txt (do NOT commit it)."
        )

HEADERS = {"Authorization": f"token {TOKEN}"}

df = pd.read_csv("workflow_runs.csv")

# Create directories
os.makedirs("logs_failure", exist_ok=True)
os.makedirs("logs_normal", exist_ok=True)

for _, row in tqdm(df.iterrows(), total=len(df)):
    log_url = row["log_url"]
    run_id = row["run_id"]
    repo = row["repo"].replace("/", "_")
    conclusion = row["conclusion"]

    # Choose directory based on conclusion
    log_dir = "logs_failure" if conclusion == "failure" else "logs_normal"

    try:
        r = requests.get(log_url, headers=HEADERS)
        z = zipfile.ZipFile(io.BytesIO(r.content))

        z.extractall(f"{log_dir}/{repo}_{run_id}")

    except Exception as e:
        print(f"Failed to download logs for run {run_id}: {e}")
