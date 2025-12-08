#!/usr/bin/env python3
"""Small end-to-end sample pipeline to collect N failed workflow runs,
download their logs, and search for memory-related keywords.

This is intended for quick demos (default N=5). It uses the same .env loader
pattern as other scripts and writes outputs under *_sample files/folders.
"""
import os
import requests
import zipfile
import io
import csv

KEYWORDS = ["137", "killed", "oom", "out of memory", "memory limit", "no memory"]


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


def fetch_runs(repos, token, max_runs=5):
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    runs = []
    for repo in repos:
        if len(runs) >= max_runs:
            break
        url = f"https://api.github.com/repos/{repo}/actions/runs?conclusion=failure&per_page=100"
        while url and len(runs) < max_runs:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            for run in data.get("workflow_runs", []):
                runs.append({
                    "repo": repo,
                    "run_id": run.get("id"),
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "log_url": run.get("logs_url"),
                })
                if len(runs) >= max_runs:
                    break

            # pagination
            link = r.headers.get("Link", "")
            next_url = None
            if link:
                for part in link.split(","):
                    if 'rel="next"' in part:
                        next_url = part.split(";")[0].strip()[1:-1]
                        break
            url = next_url

    return runs


def download_and_extract(runs, token, out_dir="logs_sample"):
    os.makedirs(out_dir, exist_ok=True)
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    for r in runs:
        log_url = r.get("log_url")
        run_id = r.get("run_id")
        repo = str(r.get("repo")).replace("/", "_")
        if not log_url:
            print(f"Skipping run {run_id}: no log_url")
            continue
        try:
            resp = requests.get(log_url, headers=headers, timeout=60)
            resp.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(resp.content))
            extract_to = os.path.join(out_dir, f"{repo}_{run_id}")
            z.extractall(extract_to)
            print(f"Extracted {run_id} to {extract_to}")
        except Exception as e:
            print(f"Failed to download/extract {run_id}: {e}")


def filter_memory_logs(search_dir="logs_sample", out_file="memory_logs_sample.txt"):
    matches = []
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith(".txt") or file.endswith(".log"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read().lower()
                    if any(k in content for k in KEYWORDS):
                        matches.append(path)
                except Exception:
                    continue

    with open(out_file, "w") as out:
        for m in matches:
            out.write(m + "\n")

    print(f"Found {len(matches)} matching logs; saved to {out_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num", type=int, default=5, help="Number of runs to collect (default 5)")
    parser.add_argument("--repos-file", default="repos.txt", help="Optional repos file (one per line)")
    args = parser.parse_args()

    _load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        # fallback to file
        if os.path.exists("github_token.txt"):
            token = open("github_token.txt").read().strip()
    if not token:
        print("ERROR: GITHUB_TOKEN not set in environment, .env, or github_token.txt")
        return

    # repos selection
    if os.path.exists(args.repos_file):
        with open(args.repos_file) as f:
            repos = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    else:
        repos = ["pytorch/pytorch", "tensorflow/tensorflow", "apache/spark"]

    print(f"Collecting up to {args.num} failed runs from {len(repos)} repos (using first matching runs)")
    runs = fetch_runs(repos, token, max_runs=args.num)
    if not runs:
        print("No runs collected.")
        return

    # write sample workflow_runs CSV
    csv_file = "workflow_runs_sample.csv"
    with open(csv_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["repo", "run_id", "status", "conclusion", "created_at", "log_url"])
        writer.writeheader()
        for r in runs:
            writer.writerow(r)

    print(f"Saved {len(runs)} runs to {csv_file}")

    download_and_extract(runs, token, out_dir="logs_sample")
    filter_memory_logs(search_dir="logs_sample", out_file="memory_logs_sample.txt")


if __name__ == "__main__":
    main()
