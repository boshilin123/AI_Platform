from __future__ import annotations


RESUME_TEXT = (
    "姓名：张三。学校：武汉理工大学。专业：软件工程。"
    "项目：使用 Spring Boot、Milvus、BM25 和大模型实现校园知识库问答。"
)
JOB_TEXT = (
    "招聘 AI 应用开发工程师，要求熟悉 Python 或 Java，具备后端服务开发能力，"
    "并有 RAG、大模型应用、Docker 或 Kubernetes 经验。"
)


def test_health_and_safe_settings(client):
    health = client.get("/api/v1/system/health")
    assert health.status_code == 200
    assert health.json()["data"]["status"] == "ok"
    assert health.headers["x-request-id"]

    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert "apiKeyConfigured" in payload
    assert "apiKey" not in payload
    assert "gptsapiApiKey" not in payload


def test_recruitment_flow_creates_audit_records(client):
    parse_response = client.post(
        "/api/v1/recruitment/resumes/parse",
        json={"resumeText": RESUME_TEXT},
        headers={"X-Caller-System": "pytest"},
    )
    assert parse_response.status_code == 200
    assert parse_response.json()["data"]["name"] == "张三"

    screening_response = client.post(
        "/api/v1/recruitment/screenings/evaluate",
        json={"resumeText": RESUME_TEXT, "jobDescription": JOB_TEXT},
        headers={"X-Caller-System": "pytest"},
    )
    assert screening_response.status_code == 200
    assert screening_response.json()["data"]["matchScore"] == 84

    interview_response = client.post(
        "/api/v1/recruitment/interview-kits/generate",
        json={
            "resumeText": RESUME_TEXT,
            "jobDescription": JOB_TEXT,
            "screeningRisks": ["评估口径待确认"],
        },
        headers={"X-Caller-System": "pytest"},
    )
    assert interview_response.status_code == 200
    assert interview_response.json()["data"]["questions"]

    audits = client.get("/api/v1/audits?page=1&pageSize=20")
    assert audits.status_code == 200
    assert audits.json()["data"]["total"] >= 3
    assert audits.json()["data"]["items"][0]["callerSystem"] == "pytest"

    dashboard = client.get("/api/v1/dashboard/overview")
    assert dashboard.status_code == 200
    assert dashboard.json()["data"]["stats"]["businessRequests"] >= 3


def test_validation_error_uses_standard_envelope(client):
    response = client.post("/api/v1/recruitment/resumes/parse", json={"resumeText": "太短"})
    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "AI_INVALID_REQUEST"
