from .agents import create_company_agent, create_onboarding_agent
from typing import Dict, Any

def load_agents(llm, system_prompt: str) -> Dict[str, Any]:
    """
    Initialize and load all chatbot agents.
    Args:
        llm: The initialized LLM instance
        system_prompt: The system prompt to use for agents
    Returns:
        Dictionary containing initialized agents
    """
    
    # Import tools
    from .tools import load_tools
    tools = load_tools()
    
    # Create different agents
    agents = {
        "chatbot": create_company_agent(llm, tools, system_prompt),
        "onboarding": create_onboarding_agent(llm, tools, system_prompt)
    }
    
    return agents