import urllib.request
import json

def get_commit_check_runs(sha):
    url = f'https://api.github.com/repos/venkatsubbarao123/DSAapp/commits/{sha}/check-runs'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Total check runs: {data.get('total_count')}")
            for cr in data.get('check_runs', []):
                print(f"ID: {cr['id']} | Name: {cr['name']} | Conclusion: {cr['conclusion']}")
                if cr['output']['title'] or cr['output']['summary']:
                    print(f"  Title: {cr['output']['title']}")
                    print(f"  Summary: {cr['output']['summary']}")
                if cr['output']['text']:
                    print(f"  Text: {cr['output']['text'][:300]}")
    except Exception as e:
        print("Error fetching check runs:", e)

if __name__ == '__main__':
    get_commit_check_runs('0c52339')
