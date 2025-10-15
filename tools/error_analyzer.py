
from __future__ import annotations
from langchain_core.tools import tool

@tool
def error_analyzer(error_message: str, code: str) -> str:
    """
    Analyzes an error message and provides insights about what might be wrong.

    Args:
        error_message: The error message from code execution
        code: The code that produced the error

    Returns:
        Analysis of the error and potential fixes
    """
    analysis = ["Error Analysis:"]

    # Common error patterns
    if "SyntaxError" in error_message:
        analysis.append("- Syntax error detected. Check for missing colons, parentheses, or incorrect indentation.")
    elif "NameError" in error_message:
        analysis.append("- Variable or function name not defined. Check variable names and imports.")
    elif "TypeError" in error_message:
        analysis.append("- Type mismatch. Check function arguments and variable types.")
    elif "IndexError" in error_message:
        analysis.append("- Index out of range. Check list/array bounds.")
    elif "KeyError" in error_message:
        analysis.append("- Dictionary key not found. Check dictionary keys.")
    elif "AttributeError" in error_message:
        analysis.append("- Attribute or method doesn't exist. Check object methods and attributes.")
    elif "ZeroDivisionError" in error_message:
        analysis.append("- Division by zero. Add validation for denominators.")
    elif "IndentationError" in error_message:
        analysis.append("- Incorrect indentation. Fix spacing and tabs.")
    else:
        analysis.append("- Check the error message carefully for clues.")

    analysis.append(f"\nCode length: {len(code.splitlines())} lines")

    return "\n".join(analysis)
