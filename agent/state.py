from typing import Optional, List, Dict, Any

from langgraph.graph.message import MessagesState
from dataclasses import dataclass, field

@dataclass
class DebugAgentState(MessagesState):
    """Extended state for the debugging agent."""
    submissions: List[Dict[str, Any]]

    iterations: int = 0
    max_iterations: int = 5
    original_buggy_code: str = ""
    test_code: str = ""
    fixed_code: str = ""
    is_fixed: bool = False
    submit_idx: int = -1
    first_pass: Optional[bool] = None
