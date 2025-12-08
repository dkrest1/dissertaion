import os
import requests
import pandas as pd
from tqdm import tqdm
import zipfile
import io


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
    try:
        TOKEN = open("github_token.txt").read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            "GitHub token not found. Set the GITHUB_TOKEN environment variable or create a local github_token.txt (do NOT commit it)."
        )

HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

df = pd.read_csv("workflow_runs.csv")

# Create directories
os.makedirs("logs_failure", exist_ok=True)
os.makedirs("logs_normal", exist_ok=True)

for _, row in tqdm(df.iterrows(), total=len(df)):
    log_url = row.get("log_url")
    run_id = row.get("run_id")
    repo = str(row.get("repo")).replace("/", "_")
    conclusion = row.get("conclusion")

    if not log_url:
        print(f"No log_url for run {run_id}, skipping")
        continue

    # Choose directory based on conclusion
    log_dir = "logs_failure" if conclusion == "failure" else "logs_normal"

    try:
        r = requests.get(log_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(f"{log_dir}/{repo}_{run_id}")

    except Exception as e:
        print(f"Failed to download logs for run {run_id}: {e}")
