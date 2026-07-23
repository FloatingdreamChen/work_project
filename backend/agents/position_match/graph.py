from __future__ import annotations

from backend.agents.position_match.nodes import (
    ask_clarification_node,
    check_hard_conditions_node,
    compliance_check_node,
    generate_answer_node,
    parse_profile_node,
    rank_positions_node,
    retrieve_policy_node,
    retrieve_positions_node,
    route_after_parse,
)
from backend.agents.position_match.state import PositionMatchState
from backend.core.graph_utils import safe_node


def build_position_match_graph():
    """Build the PositionMatchAgent LangGraph.

    Flow:
      parse_profile
      -> clarify OR retrieve_positions
      -> check_hard_conditions
      -> retrieve_policy
      -> rank_positions
      -> generate_answer
      -> compliance_check
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return _PositionMatchGraphFallback()

    builder = StateGraph(PositionMatchState)
    builder.add_node("parse_profile", safe_node("parse_profile", parse_profile_node))
    builder.add_node("ask_clarification", safe_node("ask_clarification", ask_clarification_node))
    builder.add_node("retrieve_positions", safe_node("retrieve_positions", retrieve_positions_node, {"positions": []}))
    builder.add_node("check_hard_conditions", safe_node("check_hard_conditions", check_hard_conditions_node))
    builder.add_node("retrieve_policy", safe_node("retrieve_policy", retrieve_policy_node, {"knowledge": [], "web_results": [], "sources": []}))
    builder.add_node("rank_positions", safe_node("rank_positions", rank_positions_node))
    builder.add_node("generate_answer", safe_node("generate_answer", generate_answer_node, {"answer": "岗位匹配生成失败，请查看结构化风险项。"}))
    builder.add_node("compliance_check", safe_node("compliance_check", compliance_check_node))

    builder.add_edge(START, "parse_profile")
    builder.add_conditional_edges(
        "parse_profile",
        route_after_parse,
        {
            "clarify": "ask_clarification",
            "continue": "retrieve_positions",
        },
    )
    builder.add_edge("ask_clarification", END)
    builder.add_edge("retrieve_positions", "check_hard_conditions")
    builder.add_edge("check_hard_conditions", "retrieve_policy")
    builder.add_edge("retrieve_policy", "rank_positions")
    builder.add_edge("rank_positions", "generate_answer")
    builder.add_edge("generate_answer", "compliance_check")
    builder.add_edge("compliance_check", END)
    return builder.compile()


class _PositionMatchGraphFallback:
    """Sequential executor mirroring the LangGraph flow for lightweight tests."""

    async def ainvoke(self, state: PositionMatchState, config: dict | None = None) -> PositionMatchState:
        state.update(await parse_profile_node(state))
        if route_after_parse(state) == "clarify":
            state.update(await ask_clarification_node(state))
            return state
        state.update(await retrieve_positions_node(state))
        state.update(await check_hard_conditions_node(state))
        state.update(await retrieve_policy_node(state))
        state.update(await rank_positions_node(state))
        state.update(await generate_answer_node(state))
        state.update(await compliance_check_node(state))
        return state
