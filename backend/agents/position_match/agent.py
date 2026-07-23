from __future__ import annotations

from typing import Any


DISCLAIMER = (
    "本结果不是官方资格审核结论。岗位条件、公告政策和专业目录具有时效性，"
    "请以招录机关最新公告、岗位表和人工审核为准。"
)


class PositionMatchAgent:
    """Deterministic first-pass matcher for civil service positions."""

    def match(
        self,
        profile: dict[str, Any],
        positions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        items = [self._score_position(profile, position) for position in positions]
        items.sort(key=lambda item: item["score"], reverse=True)
        return {
            "agent": "PositionMatchAgent",
            "disclaimer": DISCLAIMER,
            "items": items,
            "sources": self._sources(positions),
        }

    def _score_position(
        self, profile: dict[str, Any], position: dict[str, Any]
    ) -> dict[str, Any]:
        score = 60
        matched: list[str] = []
        risks: list[str] = []
        verification: list[str] = []

        score += self._check_contains(
            profile.get("education"),
            position.get("education_requirement"),
            "学历",
            matched,
            risks,
            verification,
            boost=12,
        )
        score += self._check_contains(
            profile.get("degree"),
            position.get("degree_requirement"),
            "学位",
            matched,
            risks,
            verification,
            boost=8,
        )
        score += self._check_major(
            profile.get("major"),
            position.get("major_requirement"),
            matched,
            risks,
            verification,
        )
        score += self._check_contains(
            profile.get("political_status"),
            position.get("political_requirement"),
            "政治面貌",
            matched,
            risks,
            verification,
            boost=8,
        )
        score += self._check_contains(
            profile.get("household_region"),
            position.get("household_requirement"),
            "户籍/生源地",
            matched,
            risks,
            verification,
            boost=6,
        )
        score += self._check_work_years(
            profile.get("work_years"),
            position.get("work_years_requirement"),
            matched,
            risks,
            verification,
        )
        score += self._check_grassroots(
            profile.get("grassroots_experience"),
            position.get("grassroots_requirement"),
            matched,
            risks,
            verification,
        )

        if risks:
            score -= min(35, len(risks) * 12)
        if verification:
            score -= min(12, len(verification) * 3)

        score = max(0, min(100, score))
        tier = "冲" if score >= 82 else "稳" if score >= 68 else "保" if score >= 55 else "不建议"
        rationale = (
            f"匹配度 {score} 分，归类为“{tier}”。"
            f"已匹配 {len(matched)} 项，风险 {len(risks)} 项，待核验 {len(verification)} 项。"
        )
        return {
            "position": position,
            "tier": tier,
            "score": score,
            "matched": matched,
            "risks": risks,
            "verification": verification,
            "rationale": rationale,
        }

    def _check_contains(
        self,
        value: Any,
        requirement: Any,
        label: str,
        matched: list[str],
        risks: list[str],
        verification: list[str],
        boost: int,
    ) -> int:
        req = self._norm(requirement)
        val = self._norm(value)
        if not req or req in {"不限", "无", "不限要求"}:
            matched.append(f"{label}：岗位未设置限制")
            return max(2, boost // 2)
        if not val:
            verification.append(f"{label}：用户画像缺失，需人工核验“{requirement}”")
            return 0
        if val in req or req in val:
            matched.append(f"{label}：{value} 符合 {requirement}")
            return boost
        risks.append(f"{label}：用户为“{value}”，岗位要求“{requirement}”")
        return -boost

    def _check_major(
        self,
        major: Any,
        requirement: Any,
        matched: list[str],
        risks: list[str],
        verification: list[str],
    ) -> int:
        req = self._norm(requirement)
        val = self._norm(major)
        if not req or "不限" in req:
            matched.append("专业：岗位未设置限制")
            return 8
        if not val:
            verification.append(f"专业：用户画像缺失，需按专业目录核验“{requirement}”")
            return 0
        if val in req or req in val:
            matched.append(f"专业：{major} 命中岗位要求")
            return 16
        if any(token and token in req for token in val.replace("与", " ").split()):
            verification.append(f"专业：可能相近，需按专业目录核验“{major}”与“{requirement}”")
            return 3
        risks.append(f"专业：{major} 未命中岗位专业要求“{requirement}”")
        return -18

    def _check_work_years(
        self,
        years: Any,
        requirement: Any,
        matched: list[str],
        risks: list[str],
        verification: list[str],
    ) -> int:
        req = self._norm(requirement)
        if not req or "不限" in req or "无" == req:
            matched.append("工作年限：岗位未设置限制")
            return 4
        if years is None:
            verification.append(f"工作年限：用户画像缺失，需核验“{requirement}”")
            return 0
        digits = [int(char) for char in req if char.isdigit()]
        required_years = max(digits) if digits else None
        if required_years is None:
            verification.append(f"工作年限：规则暂无法自动解析“{requirement}”")
            return 0
        if float(years) >= required_years:
            matched.append(f"工作年限：{years} 年满足 {requirement}")
            return 8
        risks.append(f"工作年限：{years} 年不足，岗位要求“{requirement}”")
        return -10

    def _check_grassroots(
        self,
        experience: Any,
        requirement: Any,
        matched: list[str],
        risks: list[str],
        verification: list[str],
    ) -> int:
        req = self._norm(requirement)
        val = self._norm(experience)
        if not req or "不限" in req or "无" == req:
            matched.append("基层经历：岗位未设置限制")
            return 4
        if not val:
            verification.append(f"基层经历：用户画像缺失，需核验“{requirement}”")
            return 0
        if "有" in val or "年" in val or val in req or req in val:
            matched.append(f"基层经历：{experience} 可作为初步匹配依据")
            return 8
        risks.append(f"基层经历：用户填写“{experience}”，岗位要求“{requirement}”")
        return -10

    def _sources(self, positions: list[dict[str, Any]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        sources: list[dict[str, str]] = []
        for position in positions:
            name = str(position.get("source_name") or "岗位表")
            url = str(position.get("source_url") or "")
            key = (name, url)
            if key not in seen:
                sources.append({"name": name, "url": url})
                seen.add(key)
        return sources

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower()
