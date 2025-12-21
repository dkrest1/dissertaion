#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent.parent
out_dir = root / 'docs' / 'figures'
out_dir.mkdir(parents=True, exist_ok=True)

# Load data
an = pd.read_csv(root / 'anomaly_scores.csv')
df = pd.read_csv(root / 'data_for_model.csv')

# Merge on run_dir (both files use this)
if 'run_dir' in an.columns and 'run_dir' in df.columns:
    merged = an.merge(df, on=['run_dir', 'repo', 'run_id'], how='left')
else:
    merged = an.copy()

# figure 1: histogram of anomaly scores
plt.figure(figsize=(6,4))
plt.hist(merged['score'].dropna(), bins=40, color='#3b6ea0', edgecolor='white')
plt.xlabel('Isolation Forest score')
plt.ylabel('Number of runs')
plt.title('Distribution of anomaly scores')
plt.grid(axis='y', alpha=0.2)
plt.tight_layout()
plt.savefig(out_dir / 'score_hist_300dpi.png', dpi=300)
plt.close()

# figure 2: anomalies count per repo (top 12 by count)
repo_counts = merged.groupby('repo').agg(total_runs=('run_dir','size'),
                                         anomalies=('anomaly', lambda s: s.astype(bool).sum()))
repo_counts = repo_counts.sort_values('anomalies', ascending=False)
repo_top = repo_counts.head(12)

plt.figure(figsize=(8,5))
repo_top['anomalies'].plot(kind='bar', color='#d9534f')
plt.ylabel('Anomalous runs')
plt.title('Top repositories by anomaly count')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(out_dir / 'anomalies_per_repo_300dpi.png', dpi=300)
plt.close()

# figure 3: anomaly rate per repo (repos with at least 10 runs)
repo_counts['rate'] = repo_counts['anomalies'] / repo_counts['total_runs']
repo_sample = repo_counts[repo_counts['total_runs']>=10].sort_values('rate', ascending=False).head(12)

plt.figure(figsize=(8,5))
repo_sample['rate'].plot(kind='bar', color='#5cb85c')
plt.ylabel('Anomaly rate')
plt.title('Top repositories by anomaly rate (>=10 runs)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(out_dir / 'anomaly_rate_per_repo_300dpi.png', dpi=300)
plt.close()

# figure 4: scatter kw_total vs total_size colored by anomaly
# use log scale for total_size to compress range
plt.figure(figsize=(7,5))
mask = ~merged['total_size'].isna()
xs = merged.loc[mask, 'total_size']
ys = merged.loc[mask, 'kw_total']
colors = merged.loc[mask, 'anomaly'].map({True: '#d9534f', False: '#3b6ea0'})
plt.scatter(xs, ys, c=colors, alpha=0.6, edgecolor='none')
plt.xscale('log')
plt.xlabel('Total log size (bytes, log scale)')
plt.ylabel('Total memory-related keyword count')
plt.title('Memory-keyword counts vs total log size (anomalies in red)')
plt.tight_layout()
plt.savefig(out_dir / 'kw_total_vs_size_scatter_300dpi.png', dpi=300)
plt.close()

# figure 5: boxplot of total_size by anomaly flag (log scale)
import math
vals_anom = merged.loc[merged['anomaly']==True, 'total_size'].dropna()
vals_norm = merged.loc[merged['anomaly']==False, 'total_size'].dropna()

plt.figure(figsize=(5,5))
plt.boxplot([np.log10(vals_norm[vals_norm>0]), np.log10(vals_anom[vals_anom>0])], labels=['normal','anomaly'])
plt.ylabel('log10(total_size)')
plt.title('Log of total log size: anomalies vs normal')
plt.tight_layout()
plt.savefig(out_dir / 'size_boxplot_300dpi.png', dpi=300)
plt.close()

# figure 6: average kw_total per repo (top 12 by mean kw)
mean_kw = merged.groupby('repo')['kw_total'].mean().sort_values(ascending=False).head(12)
plt.figure(figsize=(8,5))
mean_kw.plot(kind='bar', color='#f0ad4e')
plt.ylabel('Average kw_total')
plt.title('Average memory-keyword counts per repository (top 12)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(out_dir / 'avg_kw_per_repo_300dpi.png', dpi=300)
plt.close()

print('Saved figures to', out_dir)
