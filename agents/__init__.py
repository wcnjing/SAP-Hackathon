from .agents import create_company_agent, create_onboarding_agent
from .tools import acronym_meaning, who_to_ask, find_docs, load_tools
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
    
    # Import all tools (both @tool decorated and regular Tool objects)
    regular_tools = load_tools()  # Gets Tool objects from tools.py
    decorated_tools = [acronym_meaning, who_to_ask, find_docs]  # @tool decorated functions
    
    # Combine all tools
    all_tools = regular_tools + decorated_tools
    
    # Create different agents with all available tools
    agents = {
        "chatbot": create_company_agent(llm, all_tools, system_prompt),
        "onboarding": create_onboarding_agent(llm, all_tools, system_prompt)
    }
    
    return agents