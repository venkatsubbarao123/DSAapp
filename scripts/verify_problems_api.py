import httpx
import json

BASE = "http://127.0.0.1:8000/api/v1"

def run():
    client = httpx.Client(base_url=BASE, timeout=15.0)

    # 1. page=1&page_size=5
    r1 = client.get("/problems?page=1&page_size=5").json()
    d1 = r1["data"]
    print("STEP 1: page=1&page_size=5 -> items:", len(d1["items"]), "total:", d1["total"], "pages:", d1["total_pages"], "has_next:", d1["has_next"])

    # 2. page=1&page_size=20
    r2 = client.get("/problems?page=1&page_size=20").json()
    d2 = r2["data"]
    print("STEP 2: page=1&page_size=20 -> items:", len(d2["items"]), "total:", d2["total"], "pages:", d2["total_pages"])

    # 3. page=1&page_size=100
    r3 = client.get("/problems?page=1&page_size=100").json()
    d3 = r3["data"]
    print("STEP 3: page=1&page_size=100 -> items:", len(d3["items"]), "total:", d3["total"], "pages:", d3["total_pages"])

    # 4. page=2&page_size=20
    r4 = client.get("/problems?page=2&page_size=20").json()
    d4 = r4["data"]
    print("STEP 4: page=2&page_size=20 -> items:", len(d4["items"]), "page:", d4["page"], "has_prev:", d4["has_prev"], "has_next:", d4["has_next"])

    # 5. difficulty=EASY
    r5 = client.get("/problems?difficulty=EASY&page_size=1").json()
    d5 = r5["data"]
    print("STEP 5: difficulty=EASY -> total:", d5["total"])

    # 6. difficulty=MEDIUM
    r6 = client.get("/problems?difficulty=MEDIUM&page_size=1").json()
    d6 = r6["data"]
    print("STEP 6: difficulty=MEDIUM -> total:", d6["total"])

    # 7. difficulty=HARD
    r7 = client.get("/problems?difficulty=HARD&page_size=1").json()
    d7 = r7["data"]
    print("STEP 7: difficulty=HARD -> total:", d7["total"])

    # 8. problem detail
    slug1 = d1["items"][0]["slug"]
    slug2 = d1["items"][1]["slug"]
    det1 = client.get(f"/problems/{slug1}").json()["data"]
    det2 = client.get(f"/problems/{slug2}").json()["data"]
    print(f"STEP 8a: {slug1} -> title: {det1['title']}, hints: {len(det1.get('hints', []))}, sample test cases: {len(det1.get('sample_test_cases', []))}")
    print(f"STEP 8b: {slug2} -> title: {det2['title']}, hints: {len(det2.get('hints', []))}, sample test cases: {len(det2.get('sample_test_cases', []))}")

    # Additional filter tests
    r_topic = client.get("/problems?topic_slug=arrays&page_size=5").json()["data"]
    print(f"Topic 'arrays': total={r_topic['total']}")

    r_search = client.get("/problems?search=Reverse&page_size=5").json()["data"]
    print(f"Search 'Reverse': total={r_search['total']}")

if __name__ == "__main__":
    run()
