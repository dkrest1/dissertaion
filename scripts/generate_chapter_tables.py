#!/usr/bin/env python3
"""Generate summary tables for Chapter 4 from existing CSV artifacts.

Outputs:
 - docs/repo_top10_summary.csv
 - docs/dataset_summary.md
 - docs/repo_top10.md (markdown table for quick copy)
"""
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
out = root / 'docs'
out.mkdir(parents=True, exist_ok=True)

an_path = root / 'anomaly_scores.csv'
df_path = root / 'data_for_model.csv'

if not an_path.exists():
    raise SystemExit('Missing anomaly_scores.csv')
if not df_path.exists():
    raise SystemExit('Missing data_for_model.csv')

an = pd.read_csv(an_path)
df = pd.read_csv(df_path)

# Dataset summary
n_runs = len(an)
n_anom = int(an['anomaly'].astype(bool).sum())
uniq_repos = an['repo'].nunique()

with open(out / 'dataset_summary.md', 'w') as fh:
    fh.write('# Dataset summary\n\n')
    fh.write(f'- Total runs analyzed: {n_runs}\n')
    fh.write(f'- Total anomalies flagged: {n_anom}\n')
    fh.write(f'- Overall anomaly rate: {n_anom / n_runs:.2%}\n')
    fh.write(f'- Distinct repositories: {uniq_repos}\n')

# Repo level aggregation
agg = an.groupby('repo').agg(total_runs=('run_dir','size'), anomalies=('anomaly', lambda s: s.astype(bool).sum()))
agg['anomaly_rate'] = agg['anomalies'] / agg['total_runs']
agg = agg.sort_values('anomalies', ascending=False)

# Save top 10
top10 = agg.head(10).reset_index()
top10.to_csv(out / 'repo_top10_summary.csv', index=False)

# Also write a markdown table
with open(out / 'repo_top10.md', 'w') as fh:
    fh.write('| Rank | Repository | Runs analyzed | Anomalous runs | Anomaly rate |\n')
    fh.write('|---:|---|---:|---:|---:|\n')
    for i, row in top10.iterrows():
        fh.write(f'| {i+1} | {row.repo} | {row.total_runs} | {row.anomalies} | {row.anomaly_rate:.2%} |\n')

print('Wrote docs/repo_top10_summary.csv, docs/repo_top10.md, docs/dataset_summary.md')
