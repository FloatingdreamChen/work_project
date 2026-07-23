from backend.agents.position_match.graph import build_position_match_graph
from backend.agents.study_practice.graph import build_study_practice_graph
from backend.core.graph_memory import ConversationStateStore
from backend.core.retry import with_retry


POSITION_KEYWORDS = ("岗位", "职位", "报名", "专业", "资格", "户籍", "应届", "基层", "国考", "省考")
PRACTICE_KEYWORDS = ("备考", "计划", "行测", "申论", "面试", "题目", "解析", "批改", "追问")


class AgentOrchestrator:
    def __init__(self) -> None:
        self._position_graph = None
        self._study_graph = None

    def route(self, message: str) -> str:
        if any(keyword in message for keyword in POSITION_KEYWORDS):
            return "PositionMatchAgent"
        if any(keyword in message for keyword in PRACTICE_KEYWORDS):
            return "StudyPracticeAgent"
        return "StudyPracticeAgent"

    async def chat(self, message: str, conversation_id: str | None = None) -> dict:
        agent = self.route(message)
        if agent == "PositionMatchAgent":
            result = await self._chat_position(message, conversation_id)
        else:
            result = await self._chat_study(message, conversation_id)
        result["conversation_id"] = conversation_id
        return result

    @with_retry(agent_type="position_match")
    async def _chat_position(self, message: str, conversation_id: str | None = None) -> dict:
        graph = self._get_position_graph()
        remembered = ConversationStateStore.load(conversation_id)
        state = await graph.ainvoke({"user_message": message, **remembered, "conversation_id": conversation_id})
        ConversationStateStore.save(conversation_id, state)
        return {
            "answer": state.get("answer", ""),
            "agent": "PositionMatchAgent",
            "sources": state.get("sources", []),
            "fallback_used": state.get("fallback_used", False),
            "fallback_level": state.get("fallback_level"),
            "structured": state.get("structured_output"),
        }

    @with_retry(agent_type="study_practice")
    async def _chat_study(self, message: str, conversation_id: str | None = None) -> dict:
        graph = self._get_study_graph()
        remembered = ConversationStateStore.load(conversation_id)
        state = await graph.ainvoke({"user_message": message, **remembered, "conversation_id": conversation_id})
        ConversationStateStore.save(conversation_id, state)
        return {
            "answer": state.get("answer", ""),
            "agent": "StudyPracticeAgent",
            "sources": state.get("sources", []),
            "fallback_used": state.get("fallback_used", False),
            "fallback_level": state.get("fallback_level"),
            "structured": state.get("structured_output"),
        }

    def _get_position_graph(self):
        if self._position_graph is None:
            self._position_graph = build_position_match_graph()
        return self._position_graph

    def _get_study_graph(self):
        if self._study_graph is None:
            self._study_graph = build_study_practice_graph()
        return self._study_graph
