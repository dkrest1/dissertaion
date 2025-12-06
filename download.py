import os
import requests
import pandas as pd
from tqdm import tqdm
import zipfile
import io

TOKEN = open("github_token.txt").read().strip()
HEADERS = {"Authorization": f"token {TOKEN}"}

df = pd.read_csv("workflow_runs.csv")

# remove after
os.makedirs("logs", exist_ok=True)

for _, row in tqdm(df.iterrows(), total=len(df)):
    log_url = row["log_url"]
    run_id = row["run_id"]
    repo = row["repo"].replace("/", "_")

    try:
        r = requests.get(log_url, headers=HEADERS)
        z = zipfile.ZipFile(io.BytesIO(r.content))

        z.extractall(f"logs/{repo}_{run_id}")

    except Exception as e:
        print(f"Failed to download logs for run {run_id}: {e}")
