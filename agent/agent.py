
from __future__ import annotations
from typing import Any, Dict, Literal
from langchain_core.messages import SystemMessage, AIMessage

from agent.state import DebugAgentState
from tools.error_analyzer import error_analyzer
from tools.python_code_executor import python_code_executor

TOOLS = [error_analyzer, python_code_executor]

FIX_START = "<<<FIXED_CODE_START>>>"
FIX_END = "<<<FIXED_CODE_END>>>"

def _extract_fixed_code(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    if FIX_START in text and FIX_END in text:
        s = text.find(FIX_START) + len(FIX_START)
        e = text.find(FIX_END, s)
        code = text[s:e].strip()
        return code or None
    return None

def agent_node(state: DebugAgentState) -> Dict[str, Any]:

    from llm.qwen2_5_coder_7b_instruct import create_agent_llm

    """Main agent reasoning node."""

    # Check iteration limit
    if state["iterations"] >= state["max_iterations"]:
        return {
            "messages": [AIMessage(content="Maximum iterations reached. Unable to fix the code.")],
            "is_fixed": False
        }

    SYSTEM_PROMPT = f"""You are an expert Python debugging agent. Your task is to fix buggy Python code.

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
    - When providing the final fixed code, use the marker: {FIX_START} and {FIX_END}

    Example format for final answer:
    {FIX_START}
    def fixed_function():
        # corrected code here
        pass
    {FIX_END}
    
    """

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    messages = [system_msg] + state["messages"]

    llm = create_agent_llm()
    assistant = llm.bind_tools(TOOLS)

    ai_msg = assistant.invoke(messages)

    fixed_code_candidate = _extract_fixed_code(getattr(ai_msg, "content", ""))

    out: Dict[str, Any] = {
        "messages": [ai_msg],
        "iterations": state["iterations"] + 1,
    }

    if fixed_code_candidate:

        if fixed_code_candidate != state.get("fixed_code", ""):
            out["fixed_code"] = fixed_code_candidate

    return out

def tools_node(state: DebugAgentState) -> Dict[str, Any]:
    updates: Dict[str, Any] = {}

    last = state["messages"][-1] if state.get("messages") else None
    tool_msgs: list[Any] = []
    if getattr(last, "tool_calls", None):

        for tc in last.tool_calls:

            if tc["name"] == python_code_executor.name:
                args = tc["args"]
                res = python_code_executor.invoke(args)
                tool_msgs.append(res)

            elif tc["name"] == error_analyzer.name:
                args = tc["args"]
                res = error_analyzer.invoke(args)
                tool_msgs.append(res)

        if tool_msgs:
            updates["messages"] = tool_msgs

    fixed_code = state.get("fixed_code", "")

    # need submit when get fixed code and (no previous submission or fixed code is different from previous submission)
    need_submit = bool(fixed_code) and (
        not state.get("submissions") or state["submissions"][-1].get("code") != fixed_code
    )

    if need_submit:

        result = python_code_executor.invoke({
            "code": fixed_code,
            "test_code": state["test_code"]
        })

        if isinstance(result, dict):
            passed = bool(result.get("passed"))
        else:
            content = getattr(result, "content", "")
            passed = "EXIT_CODE: 0" in content and not content.startswith("ERROR:")

        runtime_ms = float(result.get("runtime_ms", 0.0)) if isinstance(result, dict) else 0.0
        stderr = result.get("stderr") if isinstance(result, dict) else None

        submit_idx = state.get("submit_idx", -1) + 1
        submissions = list(state.get("submissions", []))
        submissions.append({
            "idx": submit_idx,
            "code": fixed_code,
            "passed": passed,
            "runtime_ms": runtime_ms,
            "stderr": (stderr[:2000] if isinstance(stderr, str) else None),
        })

        updates.update({
            "submit_idx": submit_idx,
            "submissions": submissions,

            "first_pass": passed if state.get("first_pass") is None else state["first_pass"],
            "is_fixed": passed,
        })

    return updates

def should_continue(state: DebugAgentState) -> Literal["tools", "end"]:

    if state.get("is_fixed", False) or state["iterations"] >= state["max_iterations"]:
        return "end"

    last_message = state["messages"][-1] if state.get("messages") else None
    has_tool_calls = bool(getattr(last_message, "tool_calls", None))

    has_unsubmitted_candidate = False
    if state.get("fixed_code"):
        subs = state.get("submissions") or []
        has_unsubmitted_candidate = not subs or subs[-1].get("code") != state["fixed_code"]

    if has_tool_calls or has_unsubmitted_candidate:
        return "tools"

    return "end"