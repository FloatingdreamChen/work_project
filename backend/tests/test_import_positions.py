from datetime import datetime

from scripts.import_positions import _to_datetime_iso, _to_float, _to_int


def test_import_position_numeric_parsers() -> None:
    assert _to_int("1,200") == 1200
    assert _to_int("12.0") == 12
    assert _to_int("未知") is None

    assert _to_float("128.5") == 128.5
    assert _to_float("88:1") == 88
    assert _to_float("1,234.5") == 1234.5
    assert _to_float("暂无") is None


def test_import_position_date_parser() -> None:
    assert _to_datetime_iso("2026-10-14").startswith("2026-10-14")
    assert _to_datetime_iso("2026/10/14").startswith("2026-10-14")
    assert _to_datetime_iso(datetime(2026, 10, 14, 9, 30)).startswith("2026-10-14T09:30")
    assert _to_datetime_iso("待公告") == "待公告"
