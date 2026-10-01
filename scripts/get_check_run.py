import urllib.request
import json
import sys

def get_check_run_details(check_id):
    url = f'https://api.github.com/repos/venkatsubbarao123/DSAapp/check-runs/{check_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Check run output:")
            print(json.dumps(data.get('output', {}), indent=2))
    except Exception as e:
        print("Error fetching check run:", e)

    ann_url = f'https://api.github.com/repos/venkatsubbarao123/DSAapp/check-runs/{check_id}/annotations'
    areq = urllib.request.Request(ann_url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'})
    try:
        with urllib.request.urlopen(areq) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Annotations:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print("Error fetching annotations:", e)

if __name__ == '__main__':
    cid = sys.argv[1] if len(sys.argv) > 1 else '110229133024'
    get_check_run_details(cid)
