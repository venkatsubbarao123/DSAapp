import os
import sys
from pathlib import Path

# Ensure workspace root in path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///dsaapp.db"
os.environ["ALLOWED_HOSTS"] = '["localhost", "127.0.0.1", "testserver"]'
os.environ["REDIS_REQUIRED"] = "false"

import asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

async def test_apis():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health
        r = await client.get("/api/v1/health")
        print(f"/api/v1/health: status={r.status_code}")
        if r.status_code == 200:
            print(f"  Service status: {r.json()['data']['status']}")

        # 2. Curricula
        r = await client.get("/api/v1/curricula")
        data = r.json()
        items = data.get("data", [])
        print(f"\n/api/v1/curricula: status={r.status_code} -> {len(items)} curricula returned")
        for c in items:
            print(f"  - [{c.get('level')}] {c.get('title')} ({c.get('slug')})")

        # 3. Problems list
        r = await client.get("/api/v1/problems?page_size=10")
        data = r.json().get("data", {})
        total = data.get("total", 0)
        p_items = data.get("items", [])
        print(f"\n/api/v1/problems: status={r.status_code} -> Total: {total}, Page items: {len(p_items)}")

        # 4. Difficulty filtering
        for diff in ["EASY", "MEDIUM", "HARD"]:
            r = await client.get(f"/api/v1/problems?difficulty={diff}&page_size=5")
            d = r.json().get("data", {})
            print(f"  filter {diff:6s}: status={r.status_code} -> Total: {d.get('total', 0)}")

        # 5. Problem Detail
        if p_items:
            p_id = p_items[0]["id"]
            r = await client.get(f"/api/v1/problems/{p_id}")
            pd = r.json().get("data", {})
            print(f"\n/api/v1/problems/{{id}}: status={r.status_code} -> Title: '{pd.get('title')}' | Difficulty: {pd.get('difficulty')}")
            print(f"  Constraints: {pd.get('constraints')}")
            print(f"  Examples: {len(pd.get('examples', []))} | Hints: {len(pd.get('hints', []))}")

        # 6. Daily Challenge
        r = await client.get("/api/v1/practice/daily")
        raw_dc = r.json()
        print(f"\n/api/v1/practice/daily: status={r.status_code} -> Raw JSON: {raw_dc}")

        # 7. SQL problems
        r = await client.get("/api/v1/sql/problems")
        sql_data = r.json()
        sql_items = sql_data if isinstance(sql_data, list) else sql_data.get("data", [])
        print(f"\n/api/v1/sql/problems: status={r.status_code} -> {len(sql_items)} SQL problems available")

if __name__ == "__main__":
    asyncio.run(test_apis())
