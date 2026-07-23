import logging

from backend.core.compliance import POSITION_DISCLAIMER, redact_sensitive, sanitize_advice
from backend.core.logger import SensitiveDataFilter


def test_sanitize_advice_removes_forbidden_promises_and_fraud_hints() -> None:
    answer, warnings = sanitize_advice(
        "这个岗位保证录取，可以伪造证书补材料。",
        disclaimer=POSITION_DISCLAIMER,
    )

    assert "保证录取" not in answer
    assert "伪造证书" not in answer
    assert "不能承诺结果" in answer
    assert "不得伪造资格材料" in answer
    assert POSITION_DISCLAIMER in answer
    assert len(warnings) == 2


def test_redact_sensitive_nested_payload() -> None:
    payload = {
        "username": "alice",
        "password": "secret-value",
        "profile": {
            "phone": "13812345678",
            "note": "身份证 110101199001011234，Authorization: Bearer abc.def",
        },
    }

    redacted = redact_sensitive(payload)

    assert redacted["password"] == "***"
    assert redacted["profile"]["phone"] == "***"
    assert "***ID_CARD***" in redacted["profile"]["note"]
    assert "Bearer ***TOKEN***" in redacted["profile"]["note"]


def test_sensitive_data_filter_redacts_log_record_args() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="login token=%s phone=%s",
        args=("Bearer abc.def", "13812345678"),
        exc_info=None,
    )

    assert SensitiveDataFilter().filter(record) is True
    rendered = record.getMessage()
    assert "abc.def" not in rendered
    assert "13812345678" not in rendered
