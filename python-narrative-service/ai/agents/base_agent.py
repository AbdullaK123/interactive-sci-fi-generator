# ai/agents/base_agent.py
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class AgentOutput(BaseModel):
    """Base class for structured agent outputs"""
    reasoning: str = Field(description="Agent's reasoning process")
    action: str = Field(description="The action the agent decided to take")
    
class BaseAgent:
    """Base class for all narrative agents"""
    
    def __init__(self, llm, agent_name: str, agent_description: str):
        """
        Initialize a base agent
        
        Args:
            llm: The language model to use
            agent_name: Name of the agent
            agent_description: Description of the agent's role
        """
        self.llm = llm
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.memory = []  # Simple memory store
        
        # Set up basic system prompt
        self.system_prompt = SystemMessage(
            content=f"""You are {self.agent_name}, {self.agent_description}.
            Your task is to analyze the situation and determine the most appropriate action.
            Think step by step and provide your reasoning.
            """
        )
    
    async def _format_input(self, input_data: Dict[str, Any]) -> List[HumanMessage]:
        """Format input data into messages for the LLM"""
        return [HumanMessage(content=str(input_data))]
    
    async def _process_response(self, response: str) -> Dict[str, Any]:
        """Process the raw response from the LLM"""
        # Default implementation - override in subclasses
        return {"response": response}
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent on the provided input
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Agent's output
        """
        messages = [self.system_prompt] + await self._format_input(input_data)
        response = await self.llm.ainvoke(messages)
        return await self._process_response(response.content)
    
    def update_memory(self, memory_item: Any):
        """Add an item to the agent's memory"""
        self.memory.append(memory_item)
        
    def clear_memory(self):
        """Clear the agent's memory"""
        self.memory = []