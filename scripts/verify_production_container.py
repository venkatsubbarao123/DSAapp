"""Production container smoke test against the Docker image bound to PORT=10000."""
import uuid

import httpx

B = "http://127.0.0.1:10000"
ok = True

def check(label, cond, detail=""):
    global ok
    print(f"{'PASS' if cond else 'FAIL'}  {label:42s} {detail}")
    if not cond:
        ok = False

with httpx.Client(timeout=90.0) as c:
    r = c.get(f"{B}/health")
    check("/health returns 200", r.status_code == 200, f"HTTP {r.status_code}")
    check("  environment=production", r.json()["data"]["environment"] == "production")
    check("  database=connected", r.json()["data"]["database"] == "connected")

    r = c.get(f"{B}/liveness")
    check("/liveness returns 200", r.status_code == 200, f"HTTP {r.status_code}")
    r = c.get(f"{B}/readiness")
    check("/readiness returns 200", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{B}/health", headers={"Host": "dsaapp-ciys.onrender.com"})
    check("Render Host header -> 200 (was 400)", r.status_code == 200, f"HTTP {r.status_code}")

    r = c.get(f"{B}/health", headers={"Host": "evil.example.com"})
    check("Untrusted Host blocked -> 400", r.status_code == 400, f"HTTP {r.status_code}")

    p = c.get(f"{B}/api/v1/problems?page=1&page_size=1").json()["data"]
    check("415 problems", p["total"] == 415, f"total={p['total']}")

    for diff, exp in (("EASY", 144), ("MEDIUM", 186), ("HARD", 85)):
        t = c.get(f"{B}/api/v1/problems?difficulty={diff}&page_size=1").json()["data"]["total"]
        check(f"  {diff} == {exp}", t == exp, f"got {t}")

    t = c.get(f"{B}/api/v1/topics?page_size=1").json()["data"]["total"]
    check("54 topics", t == 54, f"got {t}")

    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    pw = "SmokeTest!Pass123"
    reg = c.post(f"{B}/api/v1/auth/register",
                 json={"email": email, "password": pw, "display_name": "Smoke"})
    check("register 201", reg.status_code == 201, f"HTTP {reg.status_code}")
    tok = reg.json()["data"]["access_token"]
    H = {"Authorization": f"Bearer {tok}"}

    dup = c.post(f"{B}/api/v1/auth/register", json={"email": email, "password": pw})
    check("duplicate register rejected", dup.status_code == 400, f"HTTP {dup.status_code}")

    bad = c.post(f"{B}/api/v1/auth/login", json={"email": email, "password": "Wrong!Pass123"})
    check("wrong password -> 401", bad.status_code == 401, f"HTTP {bad.status_code}")

    me = c.get(f"{B}/api/v1/auth/me", headers=H)
    check("/auth/me 200", me.status_code == 200, me.json()["data"]["email"])

    noauth = c.get(f"{B}/api/v1/auth/me")
    check("/auth/me without token -> 401", noauth.status_code == 401, f"HTTP {noauth.status_code}")

    ai = c.post(f"{B}/api/v1/ai/tutor",
                json={"problem_id": "find-maximum-in-array",
                      "question": "Explain the key idea in one sentence."}, headers=H)
    body = ai.json()
    expl = body.get("explanation", "")
    check("AI Tutor 200 + real content", ai.status_code == 200 and len(expl) > 20,
          f"HTTP {ai.status_code}, {len(expl)} chars")

    # 'user_query' must be rejected by the schema (field is 'question')
    bad_q = c.post(f"{B}/api/v1/ai/tutor",
                   json={"user_query": "wrong field name"}, headers=H)
    check("'user_query' rejected (422)", bad_q.status_code == 422,
          f"HTTP {bad_q.status_code}")

    pre = c.options(f"{B}/api/v1/auth/login",
                    headers={"Origin": "https://dsaapp.netlify.app",
                             "Access-Control-Request-Method": "POST"})
    check("CORS allows Netlify origin",
          pre.headers.get("access-control-allow-origin") == "https://dsaapp.netlify.app")

print()
print("PRODUCTION CONTAINER SMOKE TEST:", "ALL PASSED" if ok else "FAILURES PRESENT")