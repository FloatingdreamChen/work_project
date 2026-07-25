from __future__ import annotations

from backend.agents.study_practice.nodes import (
    build_plan_node,
    classify_task_node,
    compliance_check_node,
    detect_human_interrupt_node,
    generate_response_node,
    human_interrupt_node,
    retrieve_material_node,
    review_answer_node,
    route_by_interrupt,
    route_by_task_type,
    save_learning_record_node,
)
from backend.agents.study_practice.state import StudyPracticeState
from backend.core.graph_checkpointer import get_langgraph_checkpointer
from backend.core.graph_utils import safe_node


def build_study_practice_graph():
    """Build the StudyPracticeAgent LangGraph.

    Flow:
      classify_task
      -> retrieve_material
      -> build_plan OR review_answer OR generate_response
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
    builder.add_node("detect_human_interrupt", safe_node("detect_human_interrupt", detect_human_interrupt_node))
    builder.add_node("human_interrupt", safe_node("human_interrupt", human_interrupt_node))
    builder.add_node("route_task", lambda state: {})
    builder.add_node("build_plan", safe_node("build_plan", build_plan_node))
    builder.add_node("review_answer", safe_node("review_answer", review_answer_node))
    builder.add_node("generate_response", safe_node("generate_response", generate_response_node, {"answer": "备考建议生成失败，请稍后再试。"}))
    builder.add_node("compliance_check", safe_node("compliance_check", compliance_check_node))
    builder.add_node("save_learning_record", safe_node("save_learning_record", save_learning_record_node))

    builder.add_edge(START, "classify_task")
    builder.add_edge("classify_task", "retrieve_material")
    builder.add_edge("retrieve_material", "detect_human_interrupt")
    builder.add_conditional_edges(
        "detect_human_interrupt",
        route_by_interrupt,
        {
            "interrupt": "human_interrupt",
            "continue": "route_task",
        },
    )
    builder.add_conditional_edges(
        "route_task",
        route_by_task_type,
        {
            "plan": "build_plan",
            "review": "review_answer",
            "interview": "generate_response",
            "qa": "generate_response",
            "general": "generate_response",
            "optimize": "generate_response",
        },
    )
    builder.add_edge("human_interrupt", "compliance_check")
    builder.add_edge("build_plan", "generate_response")
    builder.add_edge("review_answer", "generate_response")
    builder.add_edge("generate_response", "compliance_check")
    builder.add_edge("compliance_check", "save_learning_record")
    builder.add_edge("save_learning_record", END)
    checkpointer = get_langgraph_checkpointer()
    return builder.compile(checkpointer=checkpointer) if checkpointer else builder.compile()


class _StudyPracticeGraphFallback:
    """Sequential executor mirroring the LangGraph flow for lightweight tests."""

    async def ainvoke(self, state: StudyPracticeState, config: dict | None = None) -> StudyPracticeState:
        state.update(await classify_task_node(state))
        state.update(await retrieve_material_node(state))
        state.update(await detect_human_interrupt_node(state))
        if route_by_interrupt(state) == "interrupt":
            state.update(await human_interrupt_node(state))
            state.update(await compliance_check_node(state))
            state.update(await save_learning_record_node(state))
            return state
        route = route_by_task_type(state)
        if route == "plan":
            state.update(await build_plan_node(state))
        elif route == "review":
            state.update(await review_answer_node(state))
        state.update(await generate_response_node(state))
        state.update(await compliance_check_node(state))
        state.update(await save_learning_record_node(state))
        return state
