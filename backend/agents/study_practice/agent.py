from __future__ import annotations

from datetime import date
import math

from backend.core.llm_factory import LLMFactory


DISCLAIMER = "学习建议仅用于备考参考，不承诺进面、录取或任何考试结果。"


class StudyPracticeAgent:
    def review_answer(
        self,
        practice_type: str,
        user_answer: str,
        topic: str | None = None,
        question: str | None = None,
    ) -> dict:
        text = user_answer.strip()
        strengths: list[str] = []
        problems: list[str] = []
        next_steps: list[str] = []

        if len(text) >= 120:
            strengths.append("作答较完整，具备展开分析的基础。")
        else:
            problems.append("作答偏短，论证、步骤或例证不足。")

        if any(word in text for word in ("首先", "其次", "最后", "一方面", "另一方面")):
            strengths.append("结构层次较清晰，便于阅卷或面试官抓取要点。")
        else:
            problems.append("结构标识不够明显，建议按问题、原因、对策或观点、论证、总结组织。")

        if practice_type in {"申论", "面试"} and not any(
            word in text for word in ("群众", "基层", "落实", "服务", "治理")
        ):
            problems.append("公共治理语境不足，可结合群众需求、基层执行和政策落地展开。")

        if practice_type == "行测":
            next_steps.extend(["复盘题型和错误原因", "补充同类题 10-15 道限时练习"])
        elif practice_type == "申论":
            next_steps.extend(["提炼材料关键词", "重写总分总结构的核心段落"])
        else:
            next_steps.extend(["录音复盘表达节奏", "准备 2 个真实经历例子支撑观点"])

        score = 75.0 + len(strengths) * 4 - len(problems) * 6
        score = max(45.0, min(92.0, score))
        improved_answer = self._build_improved_answer(practice_type, topic, question)

        result = {
            "agent": "StudyPracticeAgent",
            "score": score,
            "strengths": strengths or ["能围绕题目作答，具备继续打磨的基础。"],
            "problems": problems or ["下一步重点提升表达精炼度和例证质量。"],
            "improved_answer": improved_answer,
            "next_steps": next_steps,
            "disclaimer": DISCLAIMER,
        }
        if practice_type == "申论":
            result["dimension_scores"] = self._essay_dimension_scores(text)
        if practice_type == "面试":
            result["follow_up_question"] = self._interview_follow_up(text, topic)
        return result

    async def review_answer_with_ai(
        self,
        practice_type: str,
        user_answer: str,
        topic: str | None = None,
        question: str | None = None,
        knowledge: list[dict] | None = None,
    ) -> dict:
        baseline = self.review_answer(practice_type, user_answer, topic, question)
        prompt = (
            "你是公务员考试备考教练。请对用户作答做稳健、具体、可执行的批改。"
            "不得承诺考试结果，不得提供作弊建议。输出中文，包含优点、问题、优化示例和下一步训练。"
        )
        user_content = (
            f"练习类型：{practice_type}\n主题：{topic or ''}\n题目：{question or ''}\n"
            f"用户作答：{user_answer}\n规则初评：{baseline}\n知识库片段：{knowledge or []}\n"
            "请给出更细致的批改。"
        )
        ai_text = await LLMFactory.ainvoke(
            [{"role": "user", "content": user_content}],
            agent_type="study_practice",
            temperature=0.3,
            system_prompt=prompt,
        )
        baseline["ai_review"] = ai_text
        baseline["fallback_used"] = False
        return baseline

    def build_plan(
        self,
        target: str | None = None,
        weeks: int | None = None,
        exam_date: date | str | None = None,
        daily_hours: float = 2.0,
        weekly_days: int = 6,
        foundation_level: str = "零基础",
        weak_modules: list[str] | None = None,
        strong_modules: list[str] | None = None,
        preferred_modules: list[str] | None = None,
        current_scores: dict[str, float] | None = None,
        target_position: str | None = None,
        include_interview: bool = True,
    ) -> dict:
        target_name = target or "公务员考试"
        weak_modules = weak_modules or []
        strong_modules = strong_modules or []
        preferred_modules = preferred_modules or []
        current_scores = current_scores or {}

        today = date.today()
        parsed_exam_date = self._parse_date(exam_date)
        days_until_exam = (parsed_exam_date - today).days if parsed_exam_date else None
        requested_days = days_until_exam if days_until_exam and days_until_exam > 0 else None
        planned_days = max(requested_days or 90, 90)
        planned_weeks = max(13, math.ceil(planned_days / 7))
        if weeks:
            planned_weeks = max(planned_weeks, weeks, 13)
            planned_days = max(planned_days, planned_weeks * 7)

        min_cycle_enforced = bool(requested_days is not None and requested_days < 90)
        warning = (
            "距离考试不足90天，完整备考参考价值会下降；计划仍按最少3个月框架压缩执行，"
            "建议优先保基础分、抓高频题型，并人工评估是否调整报考节奏。"
            if min_cycle_enforced
            else None
        )

        weekly_hours = round(daily_hours * weekly_days, 1)
        module_weights = self._module_weights(
            foundation_level=foundation_level,
            weak_modules=weak_modules,
            strong_modules=strong_modules,
            preferred_modules=preferred_modules,
            current_scores=current_scores,
            include_interview=include_interview,
        )
        phases = self._build_phases(planned_weeks, foundation_level)
        weekly_plan = self._build_weekly_plan(
            planned_weeks=planned_weeks,
            weekly_hours=weekly_hours,
            module_weights=module_weights,
            phases=phases,
            weak_modules=weak_modules,
        )
        daily_template = self._daily_template(daily_hours, module_weights, weekly_days)
        milestones = self._milestones(planned_weeks, target_name, target_position)

        return {
            "agent": "StudyPracticeAgent",
            "target": target_name,
            "target_exam": target_name,
            "target_position": target_position,
            "exam_date": parsed_exam_date.isoformat() if parsed_exam_date else None,
            "days_until_exam": days_until_exam,
            "planned_days": planned_days,
            "planned_weeks": planned_weeks,
            "weeks": planned_weeks,
            "min_cycle_enforced": min_cycle_enforced,
            "warning": warning,
            "foundation_level": foundation_level,
            "daily_hours": daily_hours,
            "weekly_days": weekly_days,
            "weekly_hours": weekly_hours,
            "module_weights": module_weights,
            "phases": phases,
            "weekly_plan": weekly_plan,
            "plan": weekly_plan,
            "daily_template": daily_template,
            "milestones": milestones,
            "adjustment_rules": [
                "连续两周正确率低于60%的模块，下周学习时长提高20%。",
                "套题正确率稳定高于80%的模块，下周减少基础讲义时间，增加限时训练。",
                "申论小题连续两次低于目标分，优先重练材料概括和对策提炼。",
                "每周至少保留半天复盘，不新增内容，只整理错因和下周策略。",
            ],
            "disclaimer": DISCLAIMER,
        }

    def _parse_date(self, value: date | str | None) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _module_weights(
        self,
        foundation_level: str,
        weak_modules: list[str],
        strong_modules: list[str],
        preferred_modules: list[str],
        current_scores: dict[str, float],
        include_interview: bool,
    ) -> dict[str, float]:
        weights = {
            "行测-常识": 0.08,
            "行测-言语理解": 0.14,
            "行测-数量关系": 0.10,
            "行测-判断推理": 0.14,
            "行测-资料分析": 0.12,
            "申论-材料阅读": 0.14,
            "申论-小题": 0.12,
            "申论-大作文": 0.10,
        }
        if include_interview:
            weights["面试-表达与素材"] = 0.06

        if foundation_level in {"零基础", "基础薄弱"}:
            for key in ("行测-言语理解", "行测-判断推理", "申论-材料阅读"):
                weights[key] += 0.02
        elif foundation_level in {"较好", "有基础"}:
            for key in ("行测-资料分析", "申论-大作文"):
                weights[key] += 0.02

        for module in weak_modules:
            for key in weights:
                if module in key or key in module:
                    weights[key] += 0.04
        for module in strong_modules:
            for key in weights:
                if module in key or key in module:
                    weights[key] -= 0.02
        for module in preferred_modules:
            for key in weights:
                if module in key or key in module:
                    weights[key] += 0.01
        for module, score in current_scores.items():
            for key in weights:
                if module in key or key in module:
                    if score < 60:
                        weights[key] += 0.05
                    elif score >= 80:
                        weights[key] -= 0.02

        weights = {key: max(0.04, value) for key, value in weights.items()}
        total = sum(weights.values())
        return {key: round(value / total, 3) for key, value in weights.items()}

    def _build_phases(self, planned_weeks: int, foundation_level: str) -> list[dict]:
        phase_lengths = [
            max(3, round(planned_weeks * 0.25)),
            max(4, round(planned_weeks * 0.35)),
            max(3, round(planned_weeks * 0.25)),
        ]
        used = sum(phase_lengths)
        phase_lengths.append(max(1, planned_weeks - used))
        names = ["基础诊断与框架建立", "专项突破与错因归类", "套题提速与申论成文", "冲刺复盘与面试预热"]
        goals = [
            "完成行测与申论基线测试，建立错题标签和材料阅读方法。",
            "围绕薄弱模块提高正确率，形成每类题的固定解题步骤。",
            "进入整套限时训练，压缩无效耗时，提高申论输出稳定性。",
            "回看高频错因，稳定节奏，同时准备面试表达素材。",
        ]
        phases = []
        start = 1
        for name, length, goal in zip(names, phase_lengths, goals):
            end = min(planned_weeks, start + length - 1)
            phases.append({"name": name, "start_week": start, "end_week": end, "goal": goal})
            start = end + 1
            if start > planned_weeks:
                break
        if foundation_level in {"零基础", "基础薄弱"} and phases:
            phases[0]["goal"] += " 零基础阶段不要追求速度，先保证题型识别和复盘质量。"
        return phases

    def _build_weekly_plan(
        self,
        planned_weeks: int,
        weekly_hours: float,
        module_weights: dict[str, float],
        phases: list[dict],
        weak_modules: list[str],
    ) -> list[dict]:
        top_modules = sorted(module_weights.items(), key=lambda item: item[1], reverse=True)
        plan = []
        for week in range(1, planned_weeks + 1):
            phase = next((item for item in phases if item["start_week"] <= week <= item["end_week"]), phases[-1])
            focus_modules = [name for name, _ in top_modules[:3]]
            if weak_modules:
                focus_modules = list(dict.fromkeys([*weak_modules[:2], *focus_modules]))[:4]
            tasks = [
                f"{focus_modules[0]}：约{round(weekly_hours * module_weights.get(focus_modules[0], 0.12), 1)}小时，完成方法复盘和限时训练。",
                f"{focus_modules[1]}：约{round(weekly_hours * module_weights.get(focus_modules[1], 0.12), 1)}小时，整理错因标签。",
                "申论材料阅读/小题/作文至少完成2次输出。",
                "周末做一次阶段复盘，更新下周模块权重。",
            ]
            if week % 4 == 0:
                tasks.append("完成一次半套或整套模拟，记录正确率、耗时和放弃题。")
            plan.append(
                {
                    "week": week,
                    "phase": phase["name"],
                    "focus": "、".join(focus_modules[:3]),
                    "weekly_hours": weekly_hours,
                    "tasks": tasks,
                    "deliverables": [
                        "错题归因表",
                        "本周正确率/耗时记录",
                        "下周调整清单",
                    ],
                }
            )
        return plan

    def _daily_template(
        self,
        daily_hours: float,
        module_weights: dict[str, float],
        weekly_days: int,
    ) -> list[dict]:
        top_modules = [name for name, _ in sorted(module_weights.items(), key=lambda item: item[1], reverse=True)[:4]]
        warmup = round(min(0.3, daily_hours * 0.12), 1)
        main = round(max(0.5, daily_hours * 0.55), 1)
        output = round(max(0.3, daily_hours * 0.23), 1)
        review = round(max(0.2, daily_hours - warmup - main - output), 1)
        return [
            {"slot": "热身", "duration_hours": warmup, "task": "常识/言语/资料分析小题快速进入状态"},
            {"slot": "主训练", "duration_hours": main, "task": f"轮换训练：{'、'.join(top_modules[:3])}"},
            {"slot": "输出", "duration_hours": output, "task": "申论小题、作文段落或面试表达素材"},
            {"slot": "复盘", "duration_hours": review, "task": "记录错因、耗时、下次避免策略"},
            {"slot": "周休", "duration_hours": 0, "task": f"每周{7 - weekly_days}天休整或轻复盘"},
        ]

    def _milestones(self, planned_weeks: int, target: str, target_position: str | None) -> list[dict]:
        checks = [4, 8, 12, planned_weeks]
        unique_checks = []
        for week in checks:
            week = min(planned_weeks, week)
            if week not in unique_checks:
                unique_checks.append(week)
        return [
            {
                "week": week,
                "check": f"{target}{' - ' + target_position if target_position else ''}阶段评估",
                "criteria": [
                    "行测各模块正确率和耗时变化",
                    "申论小题是否能稳定按材料找点",
                    "错题是否能归因到知识、方法、审题或时间",
                ],
            }
            for week in unique_checks
        ]

    def _build_improved_answer(
        self,
        practice_type: str,
        topic: str | None,
        question: str | None,
    ) -> str:
        subject = topic or question or "这道题"
        if practice_type == "面试":
            return (
                f"对于{subject}，我会先明确问题本质，再结合岗位职责分析影响，"
                "最后提出可执行措施：一是摸清情况，二是协同资源，三是跟踪反馈，"
                "确保工作既有态度也有结果。"
            )
        if practice_type == "申论":
            return (
                f"围绕{subject}，建议按“概括问题、分析原因、提出对策”的结构展开。"
                "对策要对应材料矛盾，体现制度建设、基层执行和群众获得感。"
            )
        return f"针对{subject}，先识别题型和已知条件，再选择最短路径计算，最后用选项或边界条件校验。"

    def _essay_dimension_scores(self, text: str) -> dict[str, float]:
        reading = 70 + (8 if any(word in text for word in ("材料", "问题", "原因")) else -6)
        structure = 70 + (10 if any(word in text for word in ("首先", "其次", "最后")) else -8)
        argument = 70 + (8 if any(word in text for word in ("因为", "因此", "一方面")) else -6)
        expression = 72 + (6 if len(text) >= 160 else -8)
        policy = 68 + (10 if any(word in text for word in ("基层", "治理", "群众", "落实")) else -6)
        return {
            "reading_score": float(max(40, min(95, reading))),
            "structure_score": float(max(40, min(95, structure))),
            "argument_score": float(max(40, min(95, argument))),
            "expression_score": float(max(40, min(95, expression))),
            "policy_score": float(max(40, min(95, policy))),
        }

    def _interview_follow_up(self, text: str, topic: str | None) -> str:
        subject = topic or "刚才的观点"
        if "例" not in text and "经历" not in text:
            return f"请结合一次真实经历，说明你会如何把{subject}中的做法落到具体行动。"
        return f"如果现场资源不足，你会如何调整{subject}中的处理顺序？"
