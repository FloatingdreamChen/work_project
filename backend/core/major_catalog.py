from __future__ import annotations


MAJOR_GROUPS: dict[str, set[str]] = {
    "计算机类": {"计算机", "计算机科学与技术", "软件工程", "网络工程", "信息安全", "数据科学与大数据技术", "人工智能"},
    "法学类": {"法学", "法律", "知识产权", "政治学", "社会学"},
    "经济金融类": {"经济学", "金融学", "财政学", "税收学", "国际经济与贸易"},
    "管理类": {"工商管理", "公共管理", "行政管理", "会计学", "审计学", "财务管理"},
    "中文类": {"汉语言文学", "中文", "新闻学", "传播学", "秘书学"},
}


def normalize_major(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    for group, majors in MAJOR_GROUPS.items():
        if text == group or text in majors:
            return group
        if any(major and major in text for major in majors):
            return group
    return text


def major_matches(user_major: str | None, requirement: str | None) -> tuple[bool, bool, str]:
    """Return (matched, needs_verify, reason)."""
    req = (requirement or "").strip()
    user = (user_major or "").strip()
    if not req or "不限" in req:
        return True, False, "岗位未限制专业"
    if not user:
        return False, True, f"用户专业缺失，需按专业目录核验“{req}”"

    user_group = normalize_major(user)
    req_group = normalize_major(req)
    if user in req or req in user:
        return True, False, f"{user} 直接命中岗位专业要求"
    if user_group and user_group == req_group:
        return True, True, f"{user} 与岗位要求同属“{user_group}”，建议按官方专业目录人工核验"
    for part in req.replace("、", " ").replace(",", " ").split():
        if normalize_major(part) == user_group:
            return True, True, f"{user} 可能匹配“{part}”，需按专业目录人工核验"
    return False, False, f"{user} 未命中岗位专业要求“{req}”"


def policy_basis(source_name: str | None, source_url: str | None = None) -> dict[str, str]:
    return {
        "source_name": source_name or "岗位表",
        "source_url": source_url or "",
        "basis": "岗位表字段与招录公告要求；强时效信息需以官方最新发布为准",
    }
