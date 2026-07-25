import asyncio

from backend.agents.position_match.graph import build_position_match_graph
from backend.core.graph_memory import ConversationStateStore
from backend.core.graph_utils import safe_node


def test_conversation_state_store_merges_profile() -> None:
    ConversationStateStore.clear()
    ConversationStateStore.save("c1", {"profile": {"education": "本科"}})
    ConversationStateStore.save("c1", {"profile": {"major": "计算机"}})

    state = ConversationStateStore.load("c1")

    assert state["profile"]["education"] == "本科"
    assert state["profile"]["major"] == "计算机"


def test_conversation_state_store_async_keeps_turns_and_redacts() -> None:
    ConversationStateStore.clear()
    asyncio.run(
        ConversationStateStore.save_async(
            "c-memory",
            {"profile": {"education": "本科"}, "recent_turns": []},
            user_message="我的手机号是13812345678",
            assistant_answer="已记录你的学习偏好",
        )
    )

    state = asyncio.run(ConversationStateStore.load_async("c-memory"))

    assert state["profile"]["education"] == "本科"
    assert len(state["recent_turns"]) == 2
    assert "13812345678" not in state["recent_turns"][0]["content"]
    assert state["long_term_memory"]["profile"]["education"] == "本科"


def test_position_graph_accumulates_profile_from_prior_state() -> None:
    graph = build_position_match_graph()
    first = asyncio.run(graph.ainvoke({"user_message": "我是本科计算机专业", "conversation_id": "c2"}))
    second = asyncio.run(
        graph.ainvoke(
            {
                "user_message": "我是2027应届，想看广东国考",
                "conversation_id": "c2",
                "profile": first["profile"],
                "positions": [],
            }
        )
    )

    assert second["profile"]["education"] == "本科"
    assert "计算机" in second["profile"]["major"]
    assert second["profile"]["fresh_graduate_status"] == "应届"


def test_safe_node_converts_exception_to_state() -> None:
    async def broken(state):
        raise RuntimeError("boom")

    result = asyncio.run(safe_node("broken", broken, {"answer": "fallback"})({}))

    assert result["fallback_used"] is True
    assert result["fallback_level"] == "node:broken"
    assert result["answer"] == "fallback"
    assert result["node_errors"][0]["node"] == "broken"
