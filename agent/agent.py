
from __future__ import annotations
from typing import Any, Dict, Literal
from langchain_core.messages import SystemMessage, AIMessage

from agent.state import DebugAgentState
from tools.error_analyzer import error_analyzer
from tools.python_code_executor import python_code_executor

TOOLS = [error_analyzer, python_code_executor]

def agent_node(state: DebugAgentState) -> Dict[str, Any]:

    from llm.qwen2_5_coder_7b_instruct import create_agent_llm

    """Main agent reasoning node."""

    SYSTEM_PROMPT = """You are an expert Python debugging agent. Your task is to fix buggy Python code.

    Process:
    1. Analyze the buggy code carefully
    2. Use the execute_python_code tool to test the code and see what errors occur
    3. Use the analyze_error tool if needed to understand errors better
    4. Fix the bugs in the code
    5. Test your fix with execute_python_code
    6. If tests pass, provide the final fixed code
    7. If tests fail, iterate and try again

    Important:
    - Focus on fixing bugs, not refactoring or adding features
    - Preserve the original logic and structure when possible
    - Test your fixes before declaring success
    - Be concise in your reasoning
    - When providing the final fixed code, use the marker: <<<FIXED_CODE_START>>> and <<<FIXED_CODE_END>>>

    Example format for final answer:
    <<<FIXED_CODE_START>>>
    def fixed_function():
        # corrected code here
        pass
    <<<FIXED_CODE_END>>>
    
    """

    # Check iteration limit
    if state["iterations"] >= state["max_iterations"]:
        return {
            "messages": [AIMessage(content="Maximum iterations reached. Unable to fix the code.")],
            "is_fixed": False
        }

    # Prepare messages
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    messages = [system_msg] + state["messages"]

    # Get LLM with tools
    llm = create_agent_llm()

    assistant = llm.bind_tools(TOOLS)

    # Invoke LLM
    ai_msg = assistant.invoke(messages)

    # Check if code is fixed
    content = ai_msg.content
    is_fixed = "<<<FIXED_CODE_START>>>" in content and "<<<FIXED_CODE_END>>>" in content

    if is_fixed:
        # Extract fixed code
        start_idx = content.find("<<<FIXED_CODE_START>>>") + len("<<<FIXED_CODE_START>>>")
        end_idx = content.find("<<<FIXED_CODE_END>>>")
        fixed_code = content[start_idx:end_idx].strip()
    else:
        fixed_code = state.get("fixed_code", "")

    return {
        "messages": [ai_msg],
        "iterations": state["iterations"] + 1,
        "fixed_code": fixed_code,
        "is_fixed": is_fixed
    }

def should_continue(state: DebugAgentState) -> Literal["tools", "end"]:
    """Determine if we should continue to tools or end."""
    last_message = state["messages"][-1]

    # If agent marked as fixed or max iterations reached, end
    if state.get("is_fixed", False) or state["iterations"] >= state["max_iterations"]:
        return "end"

    # If there are tool calls, go to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "end"