
from langgraph.graph.message import MessagesState

class DebugAgentState(MessagesState):
    """Extended state for the debugging agent."""
    iterations: int = 0
    max_iterations: int = 5
    original_buggy_code: str = ""
    test_code: str = ""
    fixed_code: str = ""
    is_fixed: bool = False