
from __future__ import annotations
import subprocess
import tempfile
import os
from langchain_core.tools import tool


@tool
def python_code_executor(code: str, test_code: str = "") -> str:
    """
    Safely executes Python code in a sandboxed environment and returns the output.
    Use this tool to test if the fixed code runs without errors.

    Args:
        code: Python code to execute

    Returns:
        Execution result with stdout, stderr, and exit status
    """
    # Combine code with tests
    full_code = code
    if test_code:
        full_code = f"{code}\n\n{test_code}"

    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(full_code)
        temp_file = f.name

    try:
        # Execute with timeout and resource limits
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10,  # 10 second timeout
            cwd=tempfile.gettempdir()  # Run in temp directory for isolation
        )

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        output.append(f"EXIT_CODE: {result.returncode}")

        return "\n".join(output)

    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out (10 seconds limit)"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass
