from __future__ import annotations


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

        return {
            "agent": "StudyPracticeAgent",
            "score": score,
            "strengths": strengths or ["能围绕题目作答，具备继续打磨的基础。"],
            "problems": problems or ["下一步重点提升表达精炼度和例证质量。"],
            "improved_answer": improved_answer,
            "next_steps": next_steps,
            "disclaimer": DISCLAIMER,
        }

    def build_plan(
        self,
        target: str | None = None,
        weeks: int = 4,
    ) -> dict:
        target_name = target or "公务员考试"
        return {
            "agent": "StudyPracticeAgent",
            "target": target_name,
            "weeks": weeks,
            "plan": [
                {
                    "week": index,
                    "focus": focus,
                    "tasks": [
                        "行测模块限时训练 3 次",
                        "申论材料阅读与小题练习 2 次",
                        "复盘错题并更新薄弱点清单",
                    ],
                }
                for index, focus in enumerate(
                    ["基础诊断", "专项突破", "套题提速", "查漏补缺"][:weeks],
                    start=1,
                )
            ],
            "disclaimer": DISCLAIMER,
        }

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
