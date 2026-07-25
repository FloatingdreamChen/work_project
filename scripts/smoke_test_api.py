"""Run a real API smoke test against a running backend.

Usage:
    .venv/bin/python scripts/smoke_test_api.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test running GovExamAgent API.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--username", default=f"smoke_{int(time.time())}")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default="Smoke123456")
    return parser.parse_args()


class SmokeClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self.token = ""
        self.role = "user"

    def request(self, method: str, path: str, **kwargs) -> Any:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
        response.raise_for_status()
        if path == "/health":
            return response.json()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"{path} failed: {payload}")
        return payload["data"]

    def close(self) -> None:
        self.client.close()


def main() -> None:
    args = parse_args()
    email = args.email or f"{args.username}@example.com"
    api = SmokeClient(args.base_url)
    try:
        print("health", api.request("GET", "/health"))
        try:
            print("register", api.request("POST", "/api/v1/auth/register", json={
                "username": args.username,
                "email": email,
                "password": args.password,
            }))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 409:
                raise
            print("register skipped: user exists")

        login = api.request("POST", "/api/v1/auth/login", json={"username": args.username, "password": args.password})
        api.token = login["access_token"]
        api.role = login.get("role", "user")
        print("login", {"username": login["username"], "role": api.role})

        print("me", api.request("GET", "/api/v1/auth/me"))
        print("profile", api.request("PUT", "/api/v1/profiles/me", json={
            "target_exam": "2027国考",
            "target_region": "广东",
            "education": "本科",
            "degree": "学士",
            "major": "计算机科学与技术",
            "fresh_graduate_status": "2027应届",
            "political_status": "共青团员",
            "household_region": "广东",
            "grassroots_experience": "无",
            "work_years": 0,
        }))
        print("knowledge_status", api.request("GET", "/api/v1/knowledge/status")["vector_rag_ready"])
        print("chat", api.request("POST", "/api/v1/chat", json={
            "message": "请帮我制定申论备考计划",
            "conversation_id": f"{args.username}-conv",
        })["answer"][:80])
        print("practice_review", api.request("POST", "/api/v1/practice/review", json={
            "practice_type": "申论",
            "module_name": "申论-小题",
            "topic": "基层治理",
            "user_answer": "首先摸清群众需求，其次推动资源下沉，最后完善反馈机制。",
            "accuracy": 75,
            "duration_minutes": 20,
        })["score"])
        print("study_plan_weeks", api.request("POST", "/api/v1/practice/plan", json={
            "target_exam": "2027国考",
            "exam_date": "2027-11-28",
            "daily_hours": 2,
            "weekly_days": 6,
            "foundation_level": "一般",
            "weak_modules": ["行测-数量关系", "申论-大作文"],
            "include_interview": True,
        })["plan"]["planned_weeks"])
        interview = api.request("POST", "/api/v1/practice/interview/start", json={
            "target_position": "税务系统",
            "topic": "基层治理",
        })
        print("interview_start", interview["current_question"])
        turn = api.request("POST", "/api/v1/practice/interview/turn", json={
            "session_id": interview["session_id"],
            "question": interview["current_question"],
            "user_answer": "我会先了解诉求，再协调社区和相关部门形成解决方案。",
        })
        print("interview_turn", {"stage": turn["stage"], "question": turn["current_question"]})
        print("smoke_test=passed")
    finally:
        api.close()


if __name__ == "__main__":
    main()
