
from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agent.state import DebugAgentState
from agent.agent import agent_node, should_continue, TOOLS

def create_debug_agent_graph():
    """Create the debugging agent graph."""
    graph = StateGraph(DebugAgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(TOOLS))

    # Add edges
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    graph.add_edge("tools", "agent")

    return graph.compile()