#!/usr/bin/env python3
"""Prepare run-level features from extracted logs for model training.

Produces `data_for_model.csv` with one row per extracted run directory under
`logs_failure/` (and optionally `logs_normal/` if present). Features include
counts of files, total log size, counts of memory-related keywords, and ratios.
"""
import os
import csv
from collections import Counter

KEYWORDS = ["137", "killed", "oom", "out of memory", "memory limit", "no memory"]


def iter_run_dirs(base_dir="logs_failure"):
    if not os.path.exists(base_dir):
        return
    for name in sorted(os.listdir(base_dir)):
        path = os.path.join(base_dir, name)
        if os.path.isdir(path):
            yield name, path


def analyze_run(path):
    total_size = 0
    file_count = 0
    keyword_counts = Counter()
    text_file_count = 0

    for root, dirs, files in os.walk(path):
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                continue
            total_size += sz
            file_count += 1

            # only inspect reasonable text files
            if fn.lower().endswith((".txt", ".log", ".out", ".err", ".trace")) or sz < 200000:
                try:
                    with open(fp, "r", errors="ignore") as fh:
                        content = fh.read().lower()
                    text_file_count += 1
                    for k in KEYWORDS:
                        keyword_counts[k] += content.count(k)
                except Exception:
                    continue

    avg_file_size = (total_size / file_count) if file_count else 0
    return {
        "file_count": file_count,
        "text_file_count": text_file_count,
        "total_size": total_size,
        "avg_file_size": avg_file_size,
        **{f"kw_count_{k}": keyword_counts[k] for k in KEYWORDS},
        "kw_total": sum(keyword_counts.values()),
    }


def main():
    out_file = "data_for_model.csv"
    rows = []

    for name, path in iter_run_dirs("logs_failure"):
        # parse repo and run_id from folder name like owner_repo_12345
        parts = name.rsplit("_", 1)
        if len(parts) == 2:
            repo_str, run_id = parts
        else:
            repo_str = name
            run_id = ""

        stats = analyze_run(path)
        row = {
            "run_dir": name,
            "repo": repo_str,
            "run_id": run_id,
            "file_count": stats["file_count"],
            "text_file_count": stats["text_file_count"],
            "total_size": stats["total_size"],
            "avg_file_size": stats["avg_file_size"],
            "kw_total": stats["kw_total"],
        }
        for k in KEYWORDS:
            row[f"kw_count_{k}"] = stats[f"kw_count_{k}"]

        rows.append(row)

    if not rows:
        print("No extracted runs found under logs_failure/")
        return

    fieldnames = list(rows[0].keys())
    with open(out_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} rows to {out_file}")


if __name__ == "__main__":
    main()
