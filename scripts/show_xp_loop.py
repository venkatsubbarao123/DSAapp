"""Verifies the full judge -> XP loop: submit code, get ACCEPTED, earn XP."""
import time
import uuid

import httpx

API = "http://127.0.0.1:8000/api/v1"
c = httpx.Client(base_url=API, timeout=180.0)

email = f"xp_{uuid.uuid4().hex[:8]}@example.com"
reg = c.post("/auth/register", json={"email": email, "password": "XpTest!Pass123",
                                    "display_name": "XP Tester"})
H = {"Authorization": "Bearer " + reg.json()["data"]["access_token"]}

before = c.get("/gamification/profile", headers=H).json()
print(f"XP before submission : {before['total_xp']}")

sl = "find-maximum-in-array"
print(f"Problem              : {sl} (EASY -> 20 XP)")

code = "import sys\na=list(map(int,sys.stdin.read().split()))\nprint(max(a))\n"
sub = c.post("/submissions", json={
    "problem_id": sl, "language": "python", "source_code": code
}, headers=H)
print(f"Create submission    : HTTP {sub.status_code}")
sid = sub.json()["data"]["id"]

deadline = time.time() + 150
verdict = None
while time.time() < deadline:
    res = c.get(f"/submissions/{sid}/result", headers=H)
    if res.status_code == 200:
        d = res.json()
        if d.get("verdict"):
            verdict = d
            break
    time.sleep(3)

if verdict:
    print(f"Verdict              : {verdict['verdict']} "
          f"({verdict['tests_passed']}/{verdict['tests_total']} tests)")
else:
    print("Verdict              : TIMED OUT waiting for judge")

after = c.get("/gamification/profile", headers=H).json()
print(f"XP after submission  : {after['total_xp']}")
print(f"Level                : {before['current_level']} -> {after['current_level']}")

prog = c.get(f"/progress/problems/{sl}", headers=H).json()
print(f"Progress status      : {prog['data']['status']}")
print(f"Attempts recorded    : {prog['data']['attempts_count']}")

gain = after["total_xp"] - before["total_xp"]
print()
print(f"XP EARNED FROM JUDGE : {gain}")
print("VERDICT:", "LOOP CLOSED - judge acceptance awards XP"
      if gain > 0 else "NO XP AWARDED - needs investigation")