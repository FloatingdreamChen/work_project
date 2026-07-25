import asyncio

from backend.agents.study_practice.graph import build_study_practice_graph
from backend.config import get_settings


def test_study_graph_supports_node_level_human_interrupt() -> None:
    settings = get_settings()
    settings.enable_local_models = False
    settings.enable_milvus_rag = False
    graph = build_study_practice_graph()
    state = asyncio.run(
        graph.ainvoke(
            {
                "user_message": "这段申论请老师看一下，转人工",
                "human_interrupt": True,
            }
        )
    )

    assert state["needs_human_interrupt"] is True
    assert state["structured_output"]["needs_human_interrupt"] is True
    assert state["fallback_level"] == "human_interrupt"
