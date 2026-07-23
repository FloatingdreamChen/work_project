from backend.core.web_search_quality import (
    enrich_search_results,
    extract_published_at,
    score_source_credibility,
    source_domain,
)


def test_extract_published_at_from_common_chinese_and_iso_formats() -> None:
    assert extract_published_at("2026年10月14日发布中央机关公告") == "2026-10-14"
    assert extract_published_at("source/2026/10/15/detail.html") == "2026-10-15"
    assert extract_published_at("没有日期") is None


def test_score_source_credibility_prefers_official_sources() -> None:
    official = score_source_credibility("https://www.scs.gov.cn/kl2027/notice.html")
    forum = score_source_credibility("https://zhidao.baidu.com/question/1.html")

    assert official["level"] == "high"
    assert official["score"] > forum["score"]
    assert source_domain("https://www.scs.gov.cn/a") == "scs.gov.cn"


def test_enrich_search_results_adds_dates_import_time_and_sorts_by_credibility() -> None:
    rows = enrich_search_results(
        [
            {
                "title": "经验讨论",
                "url": "https://zhidao.baidu.com/question/1.html",
                "snippet": "2026年10月13日 有人讨论报名时间",
            },
            {
                "title": "中央机关公告",
                "url": "https://www.scs.gov.cn/notice/2026-10-14.html",
                "snippet": "考试公告",
            },
        ],
        provider="duckduckgo",
        query="2027 国考 公告",
        imported_at="2026-10-15T00:00:00+00:00",
    )

    assert rows[0]["domain"] == "scs.gov.cn"
    assert rows[0]["credibility"] == "high"
    assert rows[0]["published_at"] == "2026-10-14"
    assert rows[0]["imported_at"] == "2026-10-15T00:00:00+00:00"
    assert rows[1]["credibility"] == "low"
