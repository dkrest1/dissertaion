import os, requests, time

TOKEN=None
if os.path.exists('github_token.txt'):
    try:
        TOKEN=open('github_token.txt').read().strip()
    except Exception:
        TOKEN=None

headers={}
if TOKEN:
    headers['Authorization']=f'token {TOKEN}'

try:
    r=requests.get('https://api.github.com/rate_limit', headers=headers, timeout=15)
    print('rate_limit_status', r.status_code)
    for k in ('X-RateLimit-Limit','X-RateLimit-Remaining','X-RateLimit-Reset','Retry-After'):
        if k in r.headers:
            print(k, r.headers[k])
    if 'X-RateLimit-Reset' in r.headers:
        print('Reset UTC', time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(r.headers['X-RateLimit-Reset']))))
except Exception as e:
    print('rate_limit error', e)

# sample URL
sample=None
if os.path.exists('workflow_runs.csv'):
    with open('workflow_runs.csv') as fh:
        next(fh,None)
        line=next(fh,None)
        if line:
            parts=[p.strip() for p in line.split(',')]
            if len(parts)>=6:
                sample=parts[5].strip().strip('"')
if sample:
    print('\nSample URL:', sample)
    try:
        r2=requests.get(sample, headers=headers, timeout=20)
        print('sample_status', r2.status_code)
        for k in ('X-RateLimit-Remaining','X-RateLimit-Reset','Retry-After','Content-Length'):
            if k in r2.headers:
                print(k, r2.headers[k])
    except Exception as e:
        print('sample error', e)
else:
    print('No sample URL found in workflow_runs.csv')
