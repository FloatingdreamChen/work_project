from __future__ import annotations

from typing import Any

from backend.core.llm_factory import LLMFactory
from backend.core.major_catalog import major_matches, policy_basis


DISCLAIMER = (
    "本结果不是官方资格审核结论。岗位条件、公告政策和专业目录具有时效性，"
    "请以招录机关最新公告、岗位表和人工审核为准。"
)

MATCH_STRATEGIES = {
    "conservative": {
        "label": "稳健优先",
        "tier_thresholds": {"冲": 86, "稳": 72, "保": 58},
        "high_competition_penalty": 10,
        "medium_competition_penalty": 4,
        "large_recruitment_boost": 5,
        "previous_score_margin": 8,
    },
    "balanced": {
        "label": "均衡策略",
        "tier_thresholds": {"冲": 82, "稳": 68, "保": 55},
        "high_competition_penalty": 7,
        "medium_competition_penalty": 3,
        "large_recruitment_boost": 4,
        "previous_score_margin": 5,
    },
    "aggressive": {
        "label": "冲刺优先",
        "tier_thresholds": {"冲": 78, "稳": 64, "保": 52},
        "high_competition_penalty": 4,
        "medium_competition_penalty": 1,
        "large_recruitment_boost": 3,
        "previous_score_margin": 2,
    },
}


class PositionMatchAgent:
    """Deterministic first-pass matcher for civil service positions."""

    def match(
        self,
        profile: dict[str, Any],
        positions: list[dict[str, Any]],
        preferred_regions: list[str] | None = None,
        risk_preference: str = "balanced",
    ) -> dict[str, Any]:
        strategy = self._strategy(risk_preference)
        items = [
            self._score_position(profile, position, preferred_regions or [], strategy)
            for position in positions
        ]
        items.sort(key=lambda item: item["score"], reverse=True)
        return {
            "agent": "PositionMatchAgent",
            "disclaimer": DISCLAIMER,
            "strategy": {
                "risk_preference": risk_preference if risk_preference in MATCH_STRATEGIES else "balanced",
                "label": strategy["label"],
                "tier_thresholds": strategy["tier_thresholds"],
            },
            "items": items,
            "sources": self._sources(positions),
        }

    async def explain_with_ai(
        self,
        profile: dict[str, Any],
        positions: list[dict[str, Any]],
        rule_result: dict[str, Any] | None = None,
        knowledge: list[dict[str, Any]] | None = None,
        web_results: list[dict[str, Any]] | None = None,
        recent_turns: list[dict[str, str]] | None = None,
        long_term_memory: dict[str, Any] | None = None,
    ) -> str:
        """Ask the configured LLM to explain the rule result with compliance constraints."""
        result = rule_result or self.match(profile, positions)
        compact_items = [
            {
                "岗位": item["position"].get("position_name"),
                "部门": item["position"].get("department"),
                "分数": item["score"],
                "分类": item["tier"],
                "风险": item["risks"],
                "核验": item["verification"],
            }
            for item in result.get("items", [])[:5]
        ]
        prompt = (
            "你是考公岗位匹配助手，不是官方招录机关。请基于规则匹配结果、知识库片段和联网结果，"
            "用中文给出稳健建议。必须说明资格判断不是官方审核结论；不得承诺录取、进面或上岸；"
            "不得鼓励伪造学历、经历、证书、党员身份、基层经历。"
        )
        user_content = (
            f"用户画像：{profile}\n"
            f"长期记忆：{long_term_memory or {}}\n"
            f"最近对话：{recent_turns or []}\n"
            f"规则匹配结果：{compact_items}\n"
            f"知识库片段：{knowledge or []}\n"
            f"联网结果：{web_results or []}\n"
            "请输出：1. 总体判断；2. 冲稳保建议；3. 资格风险；4. 需人工核验材料；5. 下一步行动。"
        )
        return await LLMFactory.ainvoke(
            [{"role": "user", "content": user_content}],
            agent_type="position_match",
            temperature=0.2,
            system_prompt=prompt,
        )

    def _score_position(
        self,
        profile: dict[str, Any],
        position: dict[str, Any],
        preferred_regions: list[str],
        strategy: dict[str, Any],
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
        score += self._check_region_preference(profile, position, preferred_regions, matched)
        score += self._check_competition(position, matched, risks, strategy)
        score += self._check_previous_score(profile, position, matched, risks, verification, strategy)
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
        tier = self._tier(score, strategy["tier_thresholds"])
        rationale = (
            f"匹配度 {score} 分，按“{strategy['label']}”归类为“{tier}”。"
            f"已匹配 {len(matched)} 项，风险 {len(risks)} 项，待核验 {len(verification)} 项。"
        )
        return {
            "position": position,
            "tier": tier,
            "score": score,
            "matched": matched,
            "risks": risks,
            "verification": verification,
            "policy_basis": policy_basis(position.get("source_name"), position.get("source_url")),
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
        val = str(major or "").strip()
        is_match, needs_verify, reason = major_matches(val, str(requirement or ""))
        if is_match and not needs_verify:
            matched.append(f"专业：{reason}")
            return 8
        if is_match and needs_verify:
            verification.append(f"专业：{reason}")
            return 8
        if needs_verify:
            verification.append(f"专业：{reason}")
            return 0
        risks.append(f"专业：{reason}")
        return -18

    def _check_region_preference(
        self,
        profile: dict[str, Any],
        position: dict[str, Any],
        preferred_regions: list[str],
        matched: list[str],
    ) -> int:
        target_region = str(profile.get("target_region") or "")
        regions = [region for region in [target_region, *preferred_regions] if region]
        province = str(position.get("province") or "")
        city = str(position.get("city") or "")
        if any(region and (region in province or region in city or province in region or city in region) for region in regions):
            matched.append(f"地区偏好：岗位位于 {province}{city}，符合目标地区")
            return 5
        return 0

    def _check_competition(
        self,
        position: dict[str, Any],
        matched: list[str],
        risks: list[str],
        strategy: dict[str, Any],
    ) -> int:
        ratio = position.get("competition_ratio")
        recruitment_count = position.get("recruitment_count")
        score = 0
        if recruitment_count and int(recruitment_count) >= 3:
            matched.append(f"招录人数：计划招录 {recruitment_count} 人，机会相对更稳定")
            score += int(strategy["large_recruitment_boost"])
        if ratio is None:
            return score
        ratio = float(ratio)
        if ratio <= 30:
            matched.append(f"竞争比：约 {ratio}:1，竞争压力相对可控")
            score += 6
        elif ratio >= 100:
            risks.append(f"竞争比：约 {ratio}:1，竞争压力较高")
            score -= int(strategy["high_competition_penalty"])
        elif ratio >= 60:
            risks.append(f"竞争比：约 {ratio}:1，竞争压力偏高")
            score -= int(strategy["medium_competition_penalty"])
        return score

    def _check_previous_score(
        self,
        profile: dict[str, Any],
        position: dict[str, Any],
        matched: list[str],
        risks: list[str],
        verification: list[str],
        strategy: dict[str, Any],
    ) -> int:
        previous_min_score = position.get("previous_min_score")
        if previous_min_score is None:
            return 0
        expected_score = self._expected_written_score(profile)
        if expected_score is None:
            verification.append(f"往年分数：岗位往年最低分约 {previous_min_score}，需结合模考成绩核验")
            return 0
        margin = float(expected_score) - float(previous_min_score)
        required_margin = float(strategy["previous_score_margin"])
        if margin >= required_margin:
            matched.append(f"往年分数：模考/预估 {expected_score}，高于往年最低分约 {margin:.1f} 分")
            return 5
        if margin >= 0:
            verification.append(
                f"往年分数：模考/预估 {expected_score} 略高于往年最低分，安全边际不足 {required_margin:g} 分"
            )
            return 0
        risks.append(f"往年分数：模考/预估 {expected_score} 低于往年最低分约 {abs(margin):.1f} 分")
        return -6

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

    def _strategy(self, risk_preference: str) -> dict[str, Any]:
        return MATCH_STRATEGIES.get(risk_preference, MATCH_STRATEGIES["balanced"])

    def _tier(self, score: int, thresholds: dict[str, int]) -> str:
        if score >= thresholds["冲"]:
            return "冲"
        if score >= thresholds["稳"]:
            return "稳"
        if score >= thresholds["保"]:
            return "保"
        return "不建议"

    def _expected_written_score(self, profile: dict[str, Any]) -> float | None:
        for key in ("expected_written_score", "mock_score", "written_score"):
            value = profile.get(key)
            if value not in (None, ""):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None
        current_scores = profile.get("current_scores")
        if isinstance(current_scores, dict):
            for key in ("笔试", "总分", "行测申论", "written"):
                value = current_scores.get(key)
                if value not in (None, ""):
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return None
        return None

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower()
