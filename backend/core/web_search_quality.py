from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse


HIGH_TRUST_DOMAINS = (
    ".gov.cn",
    "gov.cn",
    "scs.gov.cn",
    "mohrss.gov.cn",
    "chinatax.gov.cn",
    "customs.gov.cn",
    "people.com.cn",
    "xinhuanet.com",
)

MEDIUM_TRUST_DOMAINS = (
    ".edu.cn",
    "edu.cn",
    "org.cn",
    "12333.gov.cn",
)

LOW_TRUST_HINTS = (
    "zhidao.baidu.com",
    "tieba.baidu.com",
    "douban.com/group",
    "csdn.net",
    "toutiao.com",
)


def enrich_search_results(
    results: list[dict],
    *,
    provider: str,
    query: str,
    imported_at: str | None = None,
) -> list[dict]:
    """Attach source quality metadata to web search results."""
    imported_at = imported_at or datetime.now(UTC).isoformat()
    enriched: list[dict] = []
    for index, item in enumerate(results, start=1):
        url = str(item.get("url") or "")
        text_parts = [
            str(item.get("title") or ""),
            str(item.get("snippet") or ""),
            str(item.get("content") or ""),
            url,
        ]
        published_at = item.get("published_at") or item.get("published_date") or extract_published_at(" ".join(text_parts))
        credibility = score_source_credibility(url)
        enriched.append(
            {
                **item,
                "rank": index,
                "provider": provider,
                "query": query,
                "domain": source_domain(url),
                "credibility": credibility["level"],
                "credibility_score": credibility["score"],
                "credibility_reason": credibility["reason"],
                "published_at": published_at,
                "imported_at": imported_at,
                "needs_date_verification": published_at is None,
            }
        )
    enriched.sort(key=lambda row: (row.get("credibility_score", 0), -int(row.get("rank", 999))), reverse=True)
    return enriched


def source_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def score_source_credibility(url: str) -> dict[str, int | str]:
    domain = source_domain(url)
    if not domain:
        return {"level": "unknown", "score": 30, "reason": "缺少来源域名，需人工核验"}
    if any(hint in domain for hint in LOW_TRUST_HINTS):
        return {"level": "low", "score": 35, "reason": "内容平台或社区来源，只能作为线索"}
    if any(domain.endswith(trusted) or trusted in domain for trusted in HIGH_TRUST_DOMAINS):
        return {"level": "high", "score": 90, "reason": "政府/权威媒体来源，优先采用"}
    if any(domain.endswith(trusted) or trusted in domain for trusted in MEDIUM_TRUST_DOMAINS):
        return {"level": "medium", "score": 70, "reason": "机构/教育来源，可作为辅助依据"}
    return {"level": "medium", "score": 55, "reason": "一般公开网页，需结合官方公告核验"}


def extract_published_at(text: str) -> str | None:
    for pattern, fmt in (
        (r"(20\d{2})[-/\.](1[0-2]|0?[1-9])[-/\.](3[01]|[12]\d|0?[1-9])", "%Y-%m-%d"),
        (r"(20\d{2})年(1[0-2]|0?[1-9])月(3[01]|[12]\d|0?[1-9])日", "%Y-%m-%d"),
    ):
        match = re.search(pattern, text)
        if match:
            year, month, day = match.groups()
            normalized = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            try:
                return datetime.strptime(normalized, fmt).date().isoformat()
            except ValueError:
                return None
    return None
