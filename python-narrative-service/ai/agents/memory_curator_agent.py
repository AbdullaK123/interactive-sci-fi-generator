# ai/agents/memory_curator_agent.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from ai.agents.base_agent import BaseAgent, AgentOutput

class MemorySelection(BaseModel):
    """Structure for a selected memory"""
    event_id: Optional[str] = Field(None, description="ID of the event if available")
    description: str = Field(description="Description of the memory")
    relevance_score: float = Field(description="How relevant this memory is (0-10)")
    recency_penalty: float = Field(description="Penalty applied for recency")

class MemoryCuratorResponse(AgentOutput):
    """Output schema for the Memory Curator Agent"""
    selected_memories: List[MemorySelection] = Field(description="Selected memories for context")
    relevance_reasoning: str = Field(description="Reasoning about memory relevance")
    
class MemoryCuratorAgent(BaseAgent):
    """Agent responsible for selecting relevant memories for context"""
    
    def __init__(self, llm, story_id: str):
        """
        Initialize a memory curator agent
        
        Args:
            llm: The language model to use
            story_id: Database ID of the story
        """
        super().__init__(
            llm=llm,
            agent_name="Memory Curator Agent",
            agent_description="An agent that selects and provides relevant past memories and events for the current context"
        )
        self.story_id = story_id
        
        # Enhanced system prompt for memory curator agent
        self.system_prompt.content = """You are the Memory Curator Agent, responsible for selecting the most relevant memories and past events for the current context.
        
        Your job is to:
        1. Evaluate all available past events and memories
        2. Select the most relevant ones for the current situation
        3. Balance between recency, importance, and relevance when selecting memories
        4. Provide these memories in a structured format for use in context generation
        
        When selecting memories, consider:
        - Thematic relevance: Does this memory relate to the current themes?
        - Character relevance: Does this memory involve characters in the current scene?
        - Causal relevance: Does this memory help explain the current situation?
        - Emotional relevance: Does this memory influence the emotional states of characters?
        - Location relevance: Did this memory occur in the current location?
        
        Your output should be a JSON object with:
        - reasoning: Your step-by-step thought process about memory selection
        - action: A brief description of memory curation
        - selected_memories: A list of selected memories with event_id, description, relevance_score, and recency_penalty
        - relevance_reasoning: Explanation of why these memories were judged most relevant
        """
    
    async def _format_input(self, input_data: Dict[str, Any]) -> List[HumanMessage]:
        """Format input data for memory curator agent"""
        current_situation = input_data.get('current_situation', '')
        available_memories = input_data.get('available_memories', [])
        active_characters = input_data.get('active_characters', [])
        current_location = input_data.get('current_location', {})
        
        character_text = ""
        if active_characters:
            character_text = "Active characters:\n" + "\n".join([f"- {c.get('name', '')}" for c in active_characters])
        
        location_text = ""
        if current_location:
            location_text = f"Current location: {current_location.get('name', '')}"
        
        memories_text = ""
        if available_memories:
            memories_text = "Available memories:\n" + "\n".join([
                f"- ID: {m.get('id', 'unknown')}, Time: {m.get('time', 'unknown')}, "
                f"Description: {m.get('description', '')}, "
                f"Importance: {m.get('importance', 1.0)}"
                for m in available_memories
            ])
        
        message = f"""
        Current situation: {current_situation}
        
        {character_text}
        
        {location_text}
        
        {memories_text}
        
        Select the most relevant memories for the current context.
        """
        
        return [HumanMessage(content=message)]
    
    async def _process_response(self, response: str) -> Dict[str, Any]:
        """Process memory curator agent response"""
        try:
            parser = JsonOutputParser(pydantic_object=MemoryCuratorResponse)
            parsed_response = parser.parse(response)
            return parsed_response
        except Exception as e:
            # Fallback for unparseable responses
            return {
                "reasoning": "Could not parse structured response",
                "action": "Curate memories",
                "selected_memories": [],
                "relevance_reasoning": "Unable to determine memory relevance"
            }