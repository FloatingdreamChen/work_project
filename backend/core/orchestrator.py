from backend.agents.position_match.graph import build_position_match_graph
from backend.agents.study_practice.graph import build_study_practice_graph
from backend.core.graph_memory import ConversationStateStore
from backend.core.query_classifier import classify_query
from backend.core.retry import with_retry


POSITION_KEYWORDS = ("岗位", "职位", "报名", "专业", "资格", "户籍", "应届", "基层", "国考", "省考")
PRACTICE_KEYWORDS = ("备考", "计划", "行测", "申论", "面试", "题目", "解析", "批改", "追问")
QUESTION_CATEGORY_LABELS = {
    "daily_chat": "日常问答",
    "position_match": "岗位匹配",
    "study_plan": "备考计划",
    "practice_review": "练习批改",
    "interview": "面试模拟",
    "knowledge_qa": "知识问答",
    "question_optimize": "问题优化",
    "fuzzy_query": "模糊查询",
}


class AgentOrchestrator:
    def __init__(self) -> None:
        self._position_graph = None
        self._study_graph = None
        self._last_route_info: dict | None = None

    def route(self, message: str, category_hint: str | None = None) -> str:
        route_info = self._route_from_hint(category_hint) if category_hint else None
        if route_info:
            self._last_route_info = route_info
            return "PositionMatchAgent" if route_info["intent"] == "position_match" else "StudyPracticeAgent"

        route_info = self._classify_question(message)
        if route_info:
            self._last_route_info = route_info
            return "PositionMatchAgent" if route_info["intent"] == "position_match" else "StudyPracticeAgent"

        classification = classify_query(message)
        if classification and classification["confidence"] >= 0.02:
            category = "position_match" if classification["intent"] == "position_match" else "fuzzy_query"
            self._last_route_info = {
                **classification,
                "category": category,
                "category_label": QUESTION_CATEGORY_LABELS[category],
            }
            return "PositionMatchAgent" if classification["intent"] == "position_match" else "StudyPracticeAgent"
        self._last_route_info = {
            "source": "keyword_fallback",
            "intent": "study_practice",
            "category": "fuzzy_query",
            "category_label": QUESTION_CATEGORY_LABELS["fuzzy_query"],
            "confidence": 0.0,
        }
        return "StudyPracticeAgent"

    def _classify_question(self, message: str) -> dict | None:
        normalized = message.strip().lower().rstrip("！？?!。.")
        if normalized in {
            "你好",
            "您好",
            "hi",
            "hello",
            "在吗",
            "你在吗",
            "嗨",
            "哈喽",
            "早上好",
            "下午好",
            "晚上好",
            "你好吗",
            "你是谁",
            "你能做什么",
            "你能干什么",
            "你能干嘛",
            "你有什么功能",
            "有什么功能",
            "功能",
        }:
            return self._route_info("daily_chat", "study_practice", "rule_intent", 0.98)

        if any(keyword in message for keyword in ("润色", "优化", "改写", "整理一下", "怎么问", "提问")):
            return self._route_info("question_optimize", "study_practice", "rule_intent", 0.88)
        if any(keyword in message for keyword in ("批改", "评分", "打分", "作答", "答案", "帮我看看")):
            return self._route_info("practice_review", "study_practice", "rule_intent", 0.9)
        if "面试" in message or "追问" in message:
            return self._route_info("interview", "study_practice", "rule_intent", 0.9)
        if any(keyword in message for keyword in ("计划", "备考", "安排", "复习", "学习路线")):
            return self._route_info("study_plan", "study_practice", "rule_intent", 0.9)

        position_hits = sum(keyword in message for keyword in POSITION_KEYWORDS)
        practice_hits = sum(keyword in message for keyword in PRACTICE_KEYWORDS)
        if position_hits > practice_hits:
            return self._route_info(
                "position_match",
                "position_match",
                "keyword_fast_path",
                min(0.95, 0.55 + (position_hits - practice_hits) * 0.1),
                scores={"position_match": position_hits, "study_practice": practice_hits},
            )
        if practice_hits > position_hits:
            return self._route_info(
                "knowledge_qa",
                "study_practice",
                "keyword_fast_path",
                min(0.95, 0.55 + (practice_hits - position_hits) * 0.1),
                scores={"position_match": position_hits, "study_practice": practice_hits},
            )

        if len(normalized) <= 12:
            return self._route_info("fuzzy_query", "study_practice", "rule_intent", 0.55)
        return None

    def _route_from_hint(self, category_hint: str | None) -> dict | None:
        if category_hint not in QUESTION_CATEGORY_LABELS:
            return None
        intent = "position_match" if category_hint == "position_match" else "study_practice"
        return self._route_info(category_hint, intent, "user_hint", 0.99)

    def _route_info(
        self,
        category: str,
        intent: str,
        source: str,
        confidence: float,
        *,
        scores: dict | None = None,
    ) -> dict:
        return {
            "source": source,
            "intent": intent,
            "category": category,
            "category_label": QUESTION_CATEGORY_LABELS[category],
            "confidence": round(confidence, 4),
            "scores": scores or {},
        }

    async def chat(self, message: str, conversation_id: str | None = None, category_hint: str | None = None) -> dict:
        agent = self.route(message, category_hint)
        if agent == "PositionMatchAgent":
            result = await self._chat_position(message, conversation_id)
        else:
            result = await self._chat_study(message, conversation_id)
        result["conversation_id"] = conversation_id
        return result

    @with_retry(agent_type="position_match")
    async def _chat_position(self, message: str, conversation_id: str | None = None) -> dict:
        graph = self._get_position_graph()
        remembered = await ConversationStateStore.load_async(conversation_id)
        state = await graph.ainvoke(
            {"user_message": message, **remembered, "conversation_id": conversation_id, "route_info": self._last_route_info},
            config=self._graph_config(conversation_id),
        )
        await ConversationStateStore.save_async(
            conversation_id,
            state,
            user_message=message,
            assistant_answer=state.get("answer", ""),
        )
        return {
            "answer": state.get("answer", ""),
            "agent": "PositionMatchAgent",
            "sources": state.get("sources", []),
            "fallback_used": state.get("fallback_used", False),
            "fallback_level": state.get("fallback_level"),
            "response_mode": state.get("response_mode"),
            "fallback_reason": state.get("fallback_reason"),
            "structured": state.get("structured_output"),
            "route": self._last_route_info,
        }

    @with_retry(agent_type="study_practice")
    async def _chat_study(self, message: str, conversation_id: str | None = None) -> dict:
        graph = self._get_study_graph()
        remembered = await ConversationStateStore.load_async(conversation_id)
        state = await graph.ainvoke(
            {"user_message": message, **remembered, "conversation_id": conversation_id, "route_info": self._last_route_info},
            config=self._graph_config(conversation_id),
        )
        await ConversationStateStore.save_async(
            conversation_id,
            state,
            user_message=message,
            assistant_answer=state.get("answer", ""),
        )
        return {
            "answer": state.get("answer", ""),
            "agent": "StudyPracticeAgent",
            "sources": state.get("sources", []),
            "fallback_used": state.get("fallback_used", False),
            "fallback_level": state.get("fallback_level"),
            "response_mode": state.get("response_mode"),
            "fallback_reason": state.get("fallback_reason"),
            "structured": state.get("structured_output"),
            "route": self._last_route_info,
        }

    def _get_position_graph(self):
        if self._position_graph is None:
            self._position_graph = build_position_match_graph()
        return self._position_graph

    def _get_study_graph(self):
        if self._study_graph is None:
            self._study_graph = build_study_practice_graph()
        return self._study_graph

    def _graph_config(self, conversation_id: str | None) -> dict:
        return {"configurable": {"thread_id": conversation_id or "anonymous"}}
