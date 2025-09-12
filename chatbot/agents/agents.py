from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from typing import Dict, Any, List, Optional

class ChatbotAgent:
    """Wrapper class for LangChain agent with a simple reply interface"""
    
    def __init__(self, executor: AgentExecutor, agent_name: str = "chatbot"):
        self.executor = executor
        self.name = agent_name
        self.chat_history = []
    
    def reply(self, message: str) -> str:
        """
        Process user message and return agent response
        Args:
            message: User input message
        Returns:
            Agent's response as string
        """
        try:
            # Include chat history in the input
            result = self.executor.invoke({
                "input": message,
                "chat_history": self.chat_history
            })
            
            response = result.get("output", "I'm sorry, I couldn't process that.")
            
            # Update chat history
            self.chat_history.extend([
                ("human", message),
                ("assistant", response)
            ])
            
            # Keep only last 10 exchanges to avoid context overflow
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
                
            return response
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def clear_history(self):
        """Clear the chat history"""
        self.chat_history = []

def create_company_agent(llm, tools: List, system_prompt: str) -> ChatbotAgent:
    """
    Create a company-specific chatbot agent
    Args:
        llm: The language model instance
        tools: List of tools available to the agent
        system_prompt: System prompt defining agent behavior
    Returns:
        ChatbotAgent instance
    """
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=3
    )
    
    return ChatbotAgent(agent_executor, "company_agent")

def create_onboarding_agent(llm, tools: List, system_prompt: str) -> ChatbotAgent:
    """
    Create an onboarding-specific agent for new employees
    Args:
        llm: The language model instance
        tools: List of tools available to the agent
        system_prompt: System prompt defining agent behavior
    Returns:
        ChatbotAgent instance
    """
    
    onboarding_prompt = f"""
    {system_prompt}
    
    You are specifically helping with employee onboarding at SAP.
    Focus on:
    - Welcome new employees warmly
    - Provide information about company policies
    - Help with IT setup and access
    - Explain company culture and values
    - Guide through initial paperwork and processes
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", onboarding_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=3
    )
    
    return ChatbotAgent(agent_executor, "onboarding_agent")