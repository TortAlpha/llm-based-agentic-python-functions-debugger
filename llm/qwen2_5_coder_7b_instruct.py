
from langchain_openai import ChatOpenAI

def create_agent_llm(
    model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
    base_url: str = "http://localhost:1234/v1", #Im using LM Studio on local machine
    api_key: str = "lm-studio",
    temperature: float = 0.1
) -> ChatOpenAI:
    """Create and configure the LLM for the agent."""
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=4096,
    )