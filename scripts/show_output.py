"""Live project output: prints the real running state of DSAapp."""
import time
import uuid

import httpx

BE = "http://127.0.0.1:8000"
FE = "http://localhost:5173"
API = f"{BE}/api/v1"

line = "-" * 68


def header(t):
    print()
    print(line)
    print(f"  {t}")
    print(line)


be = httpx.Client(base_url=API, timeout=120.0)
root = httpx.Client(timeout=120.0)

header("1. SERVERS")
print(f"  Frontend  {FE}")
print(f"  Backend   {BE}")
print(f"  API Docs  {BE}/docs")
try:
    r = root.get(f"{FE}")
    print(f"  frontend HTTP {r.status_code}  ({len(r.content)} bytes of HTML served)")
except Exception as e:
    print(f"  frontend ERROR: {e}")

header("2. HEALTH CHECK")
h = root.get(f"{BE}/health")
print(f"  HTTP {h.status_code}")
for k, v in h.json()["data"].items():
    print(f"    {k:12s} : {v}")
print(f"  /liveness  HTTP {root.get(f'{BE}/liveness').status_code}")
print(f"  /readiness HTTP {root.get(f'{BE}/readiness').status_code}")

header("3. DATABASE (Neon PostgreSQL)")
p = be.get("/problems?page=1&page_size=1").json()["data"]
print(f"  Published problems : {p['total']}")
for diff in ("EASY", "MEDIUM", "HARD"):
    t = be.get(f"/problems?difficulty={diff}&page_size=1").json()["data"]["total"]
    print(f"    {diff:7s} : {t}")
print(f"  Topics             : {be.get('/topics?page_size=1').json()['data']['total']}")

header("4. PROBLEM LIBRARY")
for q, label in (("page=1&page_size=4", "First page"),
                 ("difficulty=HARD&page_size=3", "Hard only"),
                 ("search=two&page_size=3", "Search 'two'"),
                 ("topic_slug=arrays&page_size=3", "Topic: Arrays")):
    items = be.get(f"/problems?{q}").json()["data"]
    print(f"  {label:18s} ({items['total']:>3} matches)")
    for it in items["items"]:
        print(f"     - {it['title'][:44]:46s} [{it['difficulty']}]")

header("5. AUTHENTICATION")
email = f"demo_{uuid.uuid4().hex[:8]}@example.com"
pw = "DemoUser!Pass123"
reg = be.post("/auth/register", json={"email": email, "password": pw, "display_name": "Demo User"})
print(f"  Register          : HTTP {reg.status_code}")
tok = reg.json()["data"]["access_token"]
H = {"Authorization": f"Bearer {tok}"}
dup = be.post("/auth/register", json={"email": email, "password": pw})
print(f"  Duplicate register: HTTP {dup.status_code} ({dup.json()['error']['code']})")
print(f"  Login             : HTTP {be.post('/auth/login', json={'email': email, 'password': pw}).status_code}")
bad = be.post("/auth/login", json={"email": email, "password": "WrongPass!123"})
print(f"  Wrong password    : HTTP {bad.status_code} ({bad.json()['error']['code']})")
me = be.get("/auth/me", headers=H).json()["data"]
print(f"  /auth/me          : HTTP 200 -> {me['display_name']} [{me['role']}/{me['plan']}]")
print(f"  No token          : HTTP {be.get('/auth/me').status_code} (correctly rejected)")

header("6. AI TUTOR (live Gemini)")
diag = be.get("/ai/diagnostics", headers=H).json()
header("7. ONLINE JUDGE (Docker sandbox)")
snip = "import sys\na=list(map(int,sys.stdin.read().split()))\nprint(max(a))\n"
t0 = time.time()
run = be.post("/problems/find-maximum-in-array/run",
              json={"language": "python", "source_code": snip}, headers=H).json()["data"]
print(f"  Status  : {run['status']}  {run['passed_count']}/{run['total_count']}  "
      f"({time.time()-t0:.1f}s)")
for t in run["test_cases"]:
    print(f"     case {t['case_number']}: input {t['input']!r:26s} -> "
          f"{t['actual_output'].strip()!r:6s} expected {t['expected_output']!r}")

header("8. PROGRESS / GAMIFICATION")
gam = be.get("/gamification/profile", headers=H).json()
print(f"  XP {gam['total_xp']}  |  Level {gam['current_level']}  |  Streak {gam['current_streak']}")
print(f"  Record attempt : HTTP {be.post('/progress/problems/find-maximum-in-array/attempt', headers=H).status_code}")
print(f"  Record solve   : HTTP {be.post('/progress/problems/find-maximum-in-array/solve', headers=H).status_code}")
gam2 = be.get("/gamification/profile", headers=H).json()
print(f"  After solve    : XP {gam2['total_xp']}  |  Level {gam2['current_level']}")
prog = be.get("/progress/problems/find-maximum-in-array", headers=H)
print(f"  Problem state  : HTTP {prog.status_code} -> {prog.json().get('status')}")

header("9. MISTAKES / REVISION / LEADERBOARD")
print(f"  Mistakes    : HTTP {be.get('/mistakes', headers=H).status_code}")
print(f"  Revision    : HTTP {be.get('/revision/queue', headers=H).status_code}")
print(f"  Leaderboard : HTTP {be.get('/leaderboards?category=all_time_xp&limit=3', headers=H).status_code}")

header("10. INTERVIEW MODE")
st = be.post("/interview/start",
             json={"mode": "GENERAL_SOFTWARE", "difficulty": "MEDIUM", "target_company": "Google"},
             headers=H)
sd = st.json()
print(f"  Start   : HTTP {st.status_code}  ({len(sd['questions'])} questions)")
q = sd["questions"][0]
print(f"  Answer  : HTTP {be.post(f'/interview/sessions/{sd['id']}/questions/{q['id']}/answer', json={'user_response': 'Use a hash table for O(1) lookup.', 'code_language': 'python'}, headers=H).status_code}")
rep = be.post(f"/interview/sessions/{sd['id']}/end", headers=H).json()
print(f"  Finish  : Score {rep['overall_score']}/100 ({rep['verdict']})")
print(f"  Report  : HTTP {be.get(f'/interview/sessions/{sd['id']}/report', headers=H).status_code}")

header("11. SQL / OOP")
print(f"  SQL problems : HTTP {be.get('/sql/problems', headers=H).status_code}")
print(f"  OOP pillars  : HTTP {be.get('/oop/pillars', headers=H).status_code}")
print(f"  OOP patterns : HTTP {be.get('/oop/patterns', headers=H).status_code}")

header("12. SECURITY HEADERS")
sec = root.get(f"{BE}/health")
for hk in ("x-content-type-options", "x-frame-options", "referrer-policy", "x-request-id"):
    print(f"  {hk:24s}: {sec.headers.get(hk, 'MISSING')}")

print()
print(line)
print("  LIVE OUTPUT COMPLETE")
print(line)
print(f"  Provider : {diag.get('provider')} / {diag.get('model')}")
print(f"  Status   : {diag.get('status')}")
t0 = time.time()
ai = be.post("/ai/tutor",
             json={"problem_id": "find-maximum-in-array",
                   "question": "What is the key idea behind solving this problem?"},
             headers=H)
body = ai.json()
print(f"  Response : HTTP {ai.status_code} in {time.time()-t0:.1f}s")
print(f"  Answer   : {body.get('explanation', '')[:230]}...")