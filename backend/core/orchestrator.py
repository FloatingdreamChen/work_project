from backend.agents.study_practice import StudyPracticeAgent


POSITION_KEYWORDS = ("岗位", "职位", "报名", "专业", "资格", "户籍", "应届", "基层", "国考", "省考")
PRACTICE_KEYWORDS = ("备考", "计划", "行测", "申论", "面试", "题目", "解析", "批改", "追问")


class AgentOrchestrator:
    def __init__(self) -> None:
        self.study_agent = StudyPracticeAgent()

    def route(self, message: str) -> str:
        if any(keyword in message for keyword in POSITION_KEYWORDS):
            return "PositionMatchAgent"
        if any(keyword in message for keyword in PRACTICE_KEYWORDS):
            return "StudyPracticeAgent"
        return "StudyPracticeAgent"

    def chat(self, message: str, conversation_id: str | None = None) -> dict:
        agent = self.route(message)
        if agent == "PositionMatchAgent":
            answer = (
                "我可以帮你做岗位匹配和资格风险检查。请补充学历、专业、应届身份、"
                "政治面貌、户籍、基层经历、工作年限，以及目标考试年份/地区；"
                "若已导入岗位表，可直接使用岗位匹配功能生成“冲、稳、保”组合。"
            )
        else:
            plan = self.study_agent.build_plan(target="公务员考试", weeks=4)
            answer = (
                "建议先做一次基础诊断，再进入专项训练。首月可按“基础诊断、专项突破、"
                "套题提速、查漏补缺”推进，每周固定复盘错题和申论表达。"
            )
            answer += f"\n\n下一步重点：{plan['plan'][0]['focus']}。"
        return {
            "answer": answer,
            "agent": agent,
            "sources": [],
            "conversation_id": conversation_id,
        }
