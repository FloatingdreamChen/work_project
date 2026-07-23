from __future__ import annotations

from backend.agents.study_practice.nodes import (
    build_plan_node,
    classify_task_node,
    compliance_check_node,
    generate_response_node,
    retrieve_material_node,
    review_answer_node,
    route_by_task_type,
    save_learning_record_node,
)
from backend.agents.study_practice.state import StudyPracticeState
from backend.core.graph_utils import safe_node


def build_study_practice_graph():
    """Build the StudyPracticeAgent LangGraph.

    Flow:
      classify_task
      -> retrieve_material
      -> build_plan OR review_answer
      -> generate_response
      -> compliance_check
      -> save_learning_record
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return _StudyPracticeGraphFallback()

    builder = StateGraph(StudyPracticeState)
    builder.add_node("classify_task", safe_node("classify_task", classify_task_node))
    builder.add_node("retrieve_material", safe_node("retrieve_material", retrieve_material_node, {"knowledge": [], "sources": []}))
    builder.add_node("build_plan", safe_node("build_plan", build_plan_node))
    builder.add_node("review_answer", safe_node("review_answer", review_answer_node))
    builder.add_node("generate_response", safe_node("generate_response", generate_response_node, {"answer": "备考建议生成失败，请稍后再试。"}))
    builder.add_node("compliance_check", safe_node("compliance_check", compliance_check_node))
    builder.add_node("save_learning_record", safe_node("save_learning_record", save_learning_record_node))

    builder.add_edge(START, "classify_task")
    builder.add_edge("classify_task", "retrieve_material")
    builder.add_conditional_edges(
        "retrieve_material",
        route_by_task_type,
        {
            "plan": "build_plan",
            "review": "review_answer",
        },
    )
    builder.add_edge("build_plan", "generate_response")
    builder.add_edge("review_answer", "generate_response")
    builder.add_edge("generate_response", "compliance_check")
    builder.add_edge("compliance_check", "save_learning_record")
    builder.add_edge("save_learning_record", END)
    return builder.compile()


class _StudyPracticeGraphFallback:
    """Sequential executor mirroring the LangGraph flow for lightweight tests."""

    async def ainvoke(self, state: StudyPracticeState, config: dict | None = None) -> StudyPracticeState:
        state.update(await classify_task_node(state))
        state.update(await retrieve_material_node(state))
        if route_by_task_type(state) == "plan":
            state.update(await build_plan_node(state))
        else:
            state.update(await review_answer_node(state))
        state.update(await generate_response_node(state))
        state.update(await compliance_check_node(state))
        state.update(await save_learning_record_node(state))
        return state
