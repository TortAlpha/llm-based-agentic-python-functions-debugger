# LLM-Based Agentic Python Functions Debugger

An automatic system for fixing bugs in Python code based on an LLM agent using LangGraph.

## Description

This project is an agentic system for automatic detection and fixing of bugs in Python code. The agent uses a local LLM model (qwen2.5-coder-7b-instruct via LM Studio) for iterative code testing, error analysis, and generating fixes until all tests pass or the iteration limit is reached.

### Key Features:

- **Agentic Approach**: Uses LangGraph to build a graph with reasoning and tool execution nodes
- **Iterative Fixing**: Up to 7 attempts to fix a single problem
- **Automatic Testing**: Each fix is automatically tested with provided test cases
- **Safe Execution**: Code runs in an isolated environment with timeout protection
- **Error Analysis**: Built-in analyzer for understanding error types

## Performance Metrics

On HumanEvalFix dataset (50 problems):

- **Pass@1**: ~42% - percentage of problems where the agent found a correct solution (regardless of number of attempts)
- **First Submission Accuracy**: ~30-40% - percentage of problems where the first submission was correct
- **Maximum Iterations**: 7 attempts per problem (tested for 5 iterations metric is same)

## Architecture

### System Components:

1. **Agent Node** (`agent/agent.py`)
   - Main reasoning node of the agent
   - Analyzes code and plans fixes
   - Interacts with LLM to generate solutions
   - Uses special markers `<<<FIXED_CODE_START>>>` and `<<<FIXED_CODE_END>>>` to highlight fixed code

2. **Tools Node** (`agent/agent.py`)
   - Executes tool calls (testing, error analysis)
   - Automatically tests each new version of fixed code
   - Collects execution results and statistics
   - Forms feedback for the agent

3. **State** (`agent/state.py`)
   - Extended state based on `MessagesState` from LangGraph
   - Stores message history, fix attempts, and test results
   - Tracks iteration count and problem resolution status

4. **Tools**:
   - **python_code_executor** (`tools/python_code_executor.py`) - safe Python code execution in isolated environment with 10-second timeout
   - **error_analyzer** (`tools/error_analyzer.py`) - error type analysis and potential solution suggestions

### Agent Workflow Graph:

```
START → agent_node → should_continue → tools_node → agent_node → ... → END
                          ↓
                         end
```

**Transition Logic:**
- `should_continue()` checks:
  - Has iteration limit been reached
  - Is code fixed (`is_fixed == True`)
  - Is there an untested fix candidate
  - Are there tool calls from LLM
- If problem is solved or limit reached → transition to `END`
- If there's work for tools → transition to `tools_node`
- Otherwise → transition to `END`

## 🚀 Installation

### Prerequisites:

- Python 3.9+
- LM Studio (for local LLM execution)
- qwen2.5-coder:7b-instruct model in LM Studio

### Installation Steps:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/llm-based-agentic-python-functions-debugger.git
cd llm-based-agentic-python-functions-debugger

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. For progress bars in Jupyter Notebook/Lab
pip install ipywidgets jupyterlab-widgets

# 5. Configure environment variables
cp .env.example .env
# Edit .env file and specify LangSmith API key for logs
```

### LM Studio Setup:

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load the `qwen2.5-coder:7b-instruct` model
3. Start the local server (usually at `http://localhost:1234`)
4. Ensure the model supports function calling

## Configuration

Create a `.env` file in the project root:

```env
# LLM Configuration
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio  # Any value for LM Studio
MODEL_NAME=qwen2.5-coder-7b-instruct

# Agent Configuration
MAX_ITERATIONS=7
TIMEOUT_SECONDS=10
```

## Usage

### Basic Usage via Python:

```python
from graph import create_debug_agent_graph
from agent.state import DebugAgentState
from langchain_core.messages import HumanMessage

# Create agent graph
graph = create_debug_agent_graph()

# Prepare data
buggy_code = """
def has_close_elements(numbers, threshold):
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = elem - elem2  # BUG: should be abs(elem - elem2)
                if distance < threshold:
                    return True
    return False
"""

test_code = """
def check(has_close_elements):
    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False
    
check(has_close_elements)
"""

# Run the fix
user_message = f"Fix the following Python code:\n{buggy_code} and for testing use this code: \n{test_code}"

initial_state = {
    "messages": [HumanMessage(content=user_message)],
    "original_buggy_code": buggy_code,
    "test_code": test_code,
    "max_iterations": 7,
    "iterations": 0,
    "is_fixed": False,
    "fixed_code": "",
    "submit_idx": -1,
    "submissions": [],
    "first_pass": None
}

final_state = graph.invoke(initial_state)

print(f"Code fixed: {final_state['is_fixed']}")
print(f"Iterations used: {final_state['iterations']}")
print(f"Fixed code:\n{final_state['fixed_code']}")
```

### Usage via Jupyter Notebook:

Open `evaluation/humanevalfix_eval.ipynb` and execute cells to:

1. Load the HumanEvalFix dataset
2. Run the agent on multiple problems
3. Calculate quality metrics

```python
from datasets import load_dataset
from tqdm.notebook import tqdm

# Load dataset
dataset = load_dataset("bigcode/humanevalpack", "python")
problems = list(dataset["test"])[:50]  # first 50 problems

# Run evaluation
results = []
for problem in tqdm(problems):
    result = fix_code(
        buggy_code=problem["buggy_solution"],
        test_code=problem["test"],
        max_iterations=7
    )
    results.append(result)

# Calculate metrics
from metrics.pass_at_k import estimate_pass_at_1, estimate_first_submission_accuracy

pass_at_1 = estimate_pass_at_1(results)
first_pass_acc = estimate_first_submission_accuracy(results)

print(f"Pass@1: {pass_at_1:.2%}")
print(f"First Pass Accuracy: {first_pass_acc:.2%}")
```

## Project Structure

```
llm-based-agentic-python-functions-debugger/
├── agent/                          # Main agent logic
│   ├── __init__.py
│   ├── agent.py                   # Graph nodes (agent_node, tools_node, should_continue)
│   └── state.py                   # DebugAgentState definition
│
├── tools/                          # Agent tools
│   ├── __init__.py
│   ├── python_code_executor.py    # Python code execution in sandbox
│   └── error_analyzer.py          # Error type analysis
│
├── llm/                            # LLM configuration
│   ├── __init__.py
│   └── qwen2_5_coder_7b_instruct.py  # LLM client initialization
│
├── metrics/                        # Evaluation metrics
│   ├── __init__.py
│   └── pass_at_k.py               # Pass@1 and First Submission Accuracy
│
├── evaluation/                     # Dataset evaluation
│   ├── __init__.py
│   ├── basic_test.ipynb           # Basic tests
│   └── humanevalfix_eval.ipynb    # HumanEvalFix evaluation
│
├── graph.py                        # LangGraph graph creation
├── requirements.txt                # Project dependencies
├── .env.example                    # Configuration example
└── README.md                       # This file
```

##  Main Functions and API

### `create_debug_agent_graph()`

Creates and compiles the agent graph for code fixing.

**Returns:**
- Compiled LangGraph graph

**Example:**
```python
from graph import create_debug_agent_graph
graph = create_debug_agent_graph()
```

### `fix_code(buggy_code, test_code="", max_iterations=7)`

High-level function for fixing code (defined in `evaluation/humanevalfix_eval.ipynb`).

**Parameters:**
- `buggy_code` (str): Code with bugs to fix
- `test_code` (str): Test code to verify the fix
- `max_iterations` (int): Maximum number of fix attempts

**Returns dictionary:**
```python
{
    "fixed_code": str,           # Fixed code (latest version)
    "is_fixed": bool,            # True if all tests passed
    "iterations": int,           # Number of iterations used
    "messages": List[Message],   # History of all messages in dialogue
    "submissions": List[Dict],   # History of all attempts with results
    "first_pass": bool           # True if first attempt was successful
}
```

**Structure of submissions element:**
```python
{
    "idx": int,          # Attempt sequence number
    "code": str,         # Code that was tested
    "passed": bool,      # Did tests pass
    "stderr": str        # Stderr from execution (if errors occurred)
}
```

### `python_code_executor(code: str, test_code: str = "")`

Tool for safe Python code execution.

**Parameters:**
- `code` (str): Code to execute
- `test_code` (str, optional): Additional test code

**Returns:** String with execution result in format:
```
STDOUT:
<program output>

STDERR:
<errors, if any>

EXIT_CODE: <return code>
```

### `error_analyzer(error_message: str, code: str)`

Tool for error analysis.

**Parameters:**
- `error_message` (str): Error message
- `code` (str): Code that caused the error

**Returns:** String with analysis and fix recommendations

## Metrics

### Pass@1

**Definition:** Percentage of problems for which the agent found a correct solution (regardless of number of attempts).

**Formula:**
```
Pass@1 = (number of solved problems) / (total number of problems)
```

A problem is considered solved if `is_fixed == True` in the final state.

### First Submission Accuracy (personal interest)

**Definition:** Percentage of problems where the **first** submitted code version passed all tests.

**Formula:**
```
First Submission Accuracy = (problems with first_pass=True) / (total problems)
```

This is a stricter metric showing the quality of the agent's first solution without iterations.

## How It Works

### Main Work Cycle:

1. **Initialization**: User provides buggy code and tests
2. **Agent Node**: 
   - LLM analyzes the code
   - May call tools for testing or analysis
   - Generates fixed code version
3. **Should Continue**: Checks continuation conditions
4. **Tools Node**:
   - Executes called tools
   - Automatically tests new code with tests
   - Forms feedback for the agent
5. **Repeat**: Process repeats until success or iteration limit reached

### Code Markers:

The agent uses special markers to highlight fixed code:

```python
<<<FIXED_CODE_START>>>
def corrected_function():
    # fixed code here
    pass
<<<FIXED_CODE_END>>>
```

The system automatically extracts code between markers and submits it for testing.

## Known Issues and Limitations

### 1. **Function Calling Doesn't Always Work**
- Local models (especially 7B parameters) handle tool calling worse
- LLM may ignore available tools and try to solve the problem without testing
- **Solution**: Use more powerful models (GPT-4, Claude 3.5) or add forced first call

### 2. **7 Iterations Limit**
- Complex bugs may require more attempts
- **Solution**: Increase `max_iterations` in configuration

### 3. **7B Model Performance**
- The qwen2.5-coder-7b model is smaller and weaker than GPT-4
- May struggle with complex logical errors
- **Solution**: Use more powerful models via API

### 4. **Execution Timeout**
- Code with infinite loops is terminated after 10 seconds
- May be insufficient for some tasks
- **Solution**: Increase timeout in `python_code_executor.py`

### 5. **No Caching**
- Identical code is tested repeatedly
- **Future improvement**: Add result caching

## Dependencies

Main libraries:

- **langgraph** (>=0.2.0) - graph framework for building agents
- **langchain** (>=0.3.0) - framework for working with LLMs
- **langchain-openai** (>=0.2.0) - integration with OpenAI-compatible APIs
- **datasets** (>=2.14.0) - loading HuggingFace datasets
- **python-dotenv** (>=1.0.0) - environment variable management
- **ipywidgets** - interactive widgets for Jupyter
- **tqdm** - progress bars

## 👥 Author

Roman Avanesov

## Links

- [LangChain](https://github.com/langchain-ai/langchain) - powerful framework for working with LLMs
- [LangGraph](https://github.com/langchain-ai/langgraph) - graph framework for building agentic systems
- [HumanEvalPack](https://huggingface.co/datasets/bigcode/humanevalpack) - dataset for evaluating code fixing quality
- [LM Studio](https://lmstudio.ai/) - convenient tool for running local LLMs
- [Qwen Team](https://github.com/QwenLM) - for an code-working model

---