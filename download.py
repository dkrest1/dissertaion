import os
import time
import requests
import pandas as pd
from tqdm import tqdm
import zipfile
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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

# Optional parallelism: set WORKERS env var to control number of download threads
WORKERS = int(os.environ.get("WORKERS", "8"))

# Retry/backoff settings for HTTP requests
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))
BACKOFF_FACTOR = float(os.environ.get("BACKOFF_FACTOR", "0.5"))

# Files to track progress so we can resume
PROCESSED_FILE = "downloaded_runs.txt"
FAILED_FILE = "failed_runs.txt"


def _make_session():
    s = requests.Session()
    retries = Retry(total=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET", "POST"])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def _download_and_extract_row(row, session):
    log_url = row.get("log_url")
    run_id = row.get("run_id")
    repo = str(row.get("repo")).replace("/", "_")
    conclusion = row.get("conclusion")

    if not log_url:
        return (run_id, False, "no log_url")

    log_dir = "logs_failure" if conclusion == "failure" else "logs_normal"
    outdir = f"{log_dir}/{repo}_{run_id}"

    try:
        # stream the zip to avoid large memory spikes
        with session.get(log_url, headers=HEADERS, timeout=60, stream=True) as r:
            r.raise_for_status()
            content = io.BytesIO()
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    content.write(chunk)
        content.seek(0)
        z = zipfile.ZipFile(content)
        os.makedirs(outdir, exist_ok=True)
        z.extractall(outdir)
        return (run_id, True, outdir)
    except Exception as e:
        return (run_id, False, str(e))


# Load workflow runs
df = pd.read_csv("workflow_runs.csv")

# Load processed run ids to resume
processed = set()
if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE) as fh:
        for line in fh:
            processed.add(line.strip())

# prepare failed log file
failed_fh = open(FAILED_FILE, "a")

# Create directories
os.makedirs("logs_failure", exist_ok=True)
os.makedirs("logs_normal", exist_ok=True)

rows = [row[1].to_dict() for row in df.iterrows()]

session = _make_session()

def _worker_wrapper(r):
    run_id = str(r.get("run_id"))
    if run_id in processed:
        return (run_id, True, "skipped")
    return _download_and_extract_row(r, session)

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(_worker_wrapper, r): r for r in rows}
    for fut in tqdm(as_completed(futures), total=len(futures)):
        run_id, ok, info = fut.result()
        run_id = str(run_id)
        if ok:
            # record success (skip 'skipped')
            if info != "skipped":
                with open(PROCESSED_FILE, "a") as fh:
                    fh.write(run_id + "\n")
            processed.add(run_id)
        else:
            # log failure for retry later
            failed_fh.write(f"{run_id}\t{info}\n")
            failed_fh.flush()
            print(f"Failed to download logs for run {run_id}: {info}")

failed_fh.close()
