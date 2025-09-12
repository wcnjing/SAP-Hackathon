from langchain_core.tools import Tool
from typing import List

def get_company_info(query: str) -> str:
    """Retrieve SAP company-specific information"""
    return f"Here's information about SAP for your query: {query}"

def get_hr_policies(query: str) -> str:
    """Retrieve HR policies and employee information"""
    return f"Here's HR policy information for: {query}"

def get_it_support(query: str) -> str:
    """Provide IT support information"""
    return f"Here's IT support help for: {query}"

def load_tools() -> List[Tool]:
    """Load and return all available tools for the chatbot"""
    tools = [
        Tool(
            name="company_info",
            description="Get information about SAP company, history, products",
            func=get_company_info
        ),
        Tool(
            name="hr_policies", 
            description="Get HR policies, benefits, leave information",
            func=get_hr_policies
        ),
        Tool(
            name="it_support",
            description="Get IT support and technical help",
            func=get_it_support
        )
    ]
    
    return tools