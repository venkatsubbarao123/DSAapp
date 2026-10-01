import urllib.request
import json
import sys

def get_job_logs(job_id):
    url = f'https://api.github.com/repos/venkatsubbarao123/DSAapp/actions/jobs/{job_id}/logs'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            lines = content.splitlines()
            print(f"--- Logs for job {job_id} ({len(lines)} lines) ---")
            # print error lines or last 150 lines
            for line in lines[-150:]:
                print(line)
    except Exception as e:
        print(f"Error fetching logs for {job_id}:", e)

def check_runs():
    url = 'https://api.github.com/repos/venkatsubbarao123/DSAapp/actions/runs?per_page=5'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print("Error fetching runs:", e)
        return

    runs = data.get('workflow_runs', [])
    if runs:
        latest = runs[0]
        jobs_url = latest['jobs_url']
        jreq = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(jreq) as jresp:
            jdata = json.loads(jresp.read().decode('utf-8'))
            for job in jdata.get('jobs', []):
                print(f"Job: {job['name']} (ID: {job['id']}) | Conclusion: {job['conclusion']}")
                if job['conclusion'] == 'failure':
                    get_job_logs(job['id'])

if __name__ == '__main__':
    check_runs()
