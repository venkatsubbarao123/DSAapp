import urllib.request
import json

def get_job_info(job_id):
    url = f'https://api.github.com/repos/venkatsubbarao123/DSAapp/actions/jobs/{job_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Job details:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error fetching job info for {job_id}:", e)

if __name__ == '__main__':
    get_job_info(110229484414)
