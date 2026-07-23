from __future__ import annotations

import re
from typing import Any


FORBIDDEN_PROMISES = ("必上岸", "保证进面", "保证录取", "包上岸", "包过", "稳上岸")
FRAUD_HINTS = ("伪造学历", "伪造经历", "伪造证书", "假党员", "编造基层经历", "补一个假证明")
POSITION_DISCLAIMER = "本建议不是官方资格审核结论，请以最新公告、岗位表和招录机关人工审核为准。"
STUDY_DISCLAIMER = "学习建议仅用于备考参考，不承诺进面、录取或任何考试结果。"

SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "secret",
    "secret_key",
    "id_card",
    "身份证",
    "手机号",
    "phone",
    "mobile",
}

ID_CARD_PATTERN = re.compile(r"\b\d{6}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b")
PHONE_PATTERN = re.compile(r"\b1[3-9]\d{9}\b")
TOKEN_PATTERN = re.compile(r"(?i)(bearer\s+)[a-z0-9._\-]+")


def sanitize_advice(answer: str, *, disclaimer: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    sanitized = answer
    for phrase in FORBIDDEN_PROMISES:
        if phrase in sanitized:
            sanitized = sanitized.replace(phrase, "不能承诺结果")
            warnings.append(f"移除不合规承诺：{phrase}")
    for phrase in FRAUD_HINTS:
        if phrase in sanitized:
            sanitized = sanitized.replace(phrase, "不得伪造资格材料")
            warnings.append(f"移除不合规材料建议：{phrase}")
    if disclaimer not in sanitized:
        sanitized = f"{sanitized}\n\n{disclaimer}"
    return sanitized, warnings


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if _is_sensitive_key(str(key)) else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    if not isinstance(value, str):
        return value
    redacted = ID_CARD_PATTERN.sub("***ID_CARD***", value)
    redacted = PHONE_PATTERN.sub("***PHONE***", redacted)
    redacted = TOKEN_PATTERN.sub(r"\1***TOKEN***", redacted)
    return redacted


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(item.lower() in lowered for item in SENSITIVE_KEYS)
