from __future__ import annotations

import sys
import time
from typing import Any

import httpx


BASE_URL = "http://127.0.0.1:8000/api/v1"
PASSWORD = "SmokeTest123"


SAMPLE_POSITIONS = [
    {
        "exam_year": 2027,
        "exam_type": "国考",
        "province": "广东",
        "city": "深圳",
        "department": "国家税务总局深圳市税务局",
        "position_name": "一级行政执法员",
        "position_code": "SMOKE-300110001001",
        "recruitment_count": 2,
        "applicant_count": 46,
        "competition_ratio": 23,
        "previous_min_score": 128.5,
        "education_requirement": "本科及以上",
        "degree_requirement": "学士及以上",
        "major_requirement": "计算机科学与技术、软件工程、网络工程",
        "political_requirement": "不限",
        "grassroots_requirement": "不限",
        "work_years_requirement": "不限",
        "household_requirement": "不限",
        "source_name": "Smoke 样例岗位表",
    }
]


def unwrap(response: httpx.Response) -> Any:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{response.status_code} {response.request.method} {response.request.url}: {response.text}") from exc
    payload = response.json()
    if payload.get("code") != 0:
        raise RuntimeError(payload)
    return payload["data"]


def main() -> int:
    suffix = int(time.time())
    username = f"smoke_{suffix}"
    email = f"{username}@example.com"
    with httpx.Client(base_url=BASE_URL, timeout=20.0) as client:
        unwrap(client.post("/auth/register", json={"username": username, "email": email, "password": PASSWORD}))
        token_data = unwrap(client.post("/auth/login", json={"username": username, "password": PASSWORD}))
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        imported = unwrap(client.post("/positions/import", json={"positions": SAMPLE_POSITIONS}, headers=headers))
        report = unwrap(client.post("/practice/report", json={"days": 30}, headers=headers))
        chat = unwrap(
            client.post(
                "/chat",
                json={"message": "你好", "conversation_id": f"smoke-{suffix}", "category_hint": "daily_chat"},
                headers=headers,
            )
        )

    print("register/login: ok")
    print(f"positions/import: count={imported['count']}")
    print(f"practice/report: practice_count={report['practice_count']} days={report['days']}")
    print(f"chat: agent={chat['agent']} category={chat['route']['category']} answer={chat['answer'][:40]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
