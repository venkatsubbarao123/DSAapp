"""Verify end-to-end AI Mock Interview API flow."""

import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def test_interview_flow():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        import uuid
        test_email = f"interview_tester_{uuid.uuid4().hex[:6]}@dsaapp.dev"
        test_pass = "Password123"
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": test_email,
            "password": test_pass,
        })
        print("Registration status:", reg_res.status_code)
        assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
        token = reg_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Start Interview via /api/v1/interview/start
        start_res = await client.post("/api/v1/interview/start", json={
            "mode": "GENERAL_SOFTWARE",
            "duration_minutes": 30,
        }, headers=headers)
        print("Start interview status:", start_res.status_code)
        assert start_res.status_code == 201, f"Start failed: {start_res.text}"
        session_data = start_res.json()
        session_id = session_data["id"]
        questions = session_data["questions"]
        print(f"Session ID: {session_id}, Questions: {len(questions)}")
        assert len(questions) > 0, "No questions returned!"
        first_q = questions[0]
        assert "title" in first_q, f"Missing title in question: {first_q}"
        assert "question_text" in first_q, f"Missing question_text in question: {first_q}"
        print(f"First Question: sequence={first_q['sequence']}, title='{first_q['title']}'")

        # 3. Answer First Question via /api/v1/interview/sessions/{session_id}/questions/{question_id}/answer
        answer_res = await client.post(
            f"/api/v1/interview/sessions/{session_id}/questions/{first_q['id']}/answer",
            json={"user_response": "O(log N)"},
            headers=headers,
        )
        print("Answer status:", answer_res.status_code)
        assert answer_res.status_code == 200, f"Answer failed: {answer_res.text}"

        # 4. End Interview Session via /api/v1/interview/sessions/{session_id}/end
        end_res = await client.post(
            f"/api/v1/interview/sessions/{session_id}/end",
            headers=headers,
        )
        print("End session status:", end_res.status_code)
        assert end_res.status_code == 200, f"End session failed: {end_res.text}"
        report = end_res.json()
        print("Report verdict:", report.get("verdict"), "Overall score:", report.get("overall_score"))
        assert "overall_score" in report, "Report missing overall_score"
        assert "rubric_breakdown" in report, "Report missing rubric_breakdown"

        # 5. Fetch Report via /api/v1/interview/sessions/{session_id}/report
        get_rep = await client.get(
            f"/api/v1/interview/sessions/{session_id}/report",
            headers=headers,
        )
        print("Get report status:", get_rep.status_code)
        assert get_rep.status_code == 200, f"Get report failed: {get_rep.text}"

        print("\n[SUCCESS] AI Mock Interview end-to-end API flow passed 100%!")

if __name__ == "__main__":
    asyncio.run(test_interview_flow())
