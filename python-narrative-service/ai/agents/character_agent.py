# ai/agents/character_agent.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from ai.agents.base_agent import BaseAgent, AgentOutput

class CharacterResponse(AgentOutput):
    """Output schema for the Character Agent"""
    dialogue: Optional[str] = Field(None, description="Character's dialogue")
    emotions: Dict[str, float] = Field(default_factory=dict, description="Character's emotional state")
    motivation: str = Field(description="Character's current motivation")
    
class CharacterAgent(BaseAgent):
    """Agent responsible for maintaining character consistency and generating responses"""
    
    def __init__(self, llm, character_id: str, character_data: Dict[str, Any]):
        """
        Initialize a character agent
        
        Args:
            llm: The language model to use
            character_id: Database ID of the character
            character_data: Initial character data (name, description, traits, etc.)
        """
        super().__init__(
            llm=llm,
            agent_name=character_data['name'],
            agent_description=f"A character agent that maintains the consistent personality and actions of {character_data['name']}"
        )
        self.character_id = character_id
        self.character_data = character_data
        
        # Enhanced system prompt for character agent
        self.system_prompt.content = f"""You are {self.agent_name}, {self.agent_description}.
        
        Character Details:
        - Name: {character_data['name']}
        - Description: {character_data['description']}
        
        Character Traits:
        {self._format_traits(character_data.get('traits', {}))}
        
        Your job is to:
        1. Maintain the consistent personality of {character_data['name']} based on their traits and history
        2. Generate reactions, dialogue, and decisions that the character would make in response to events
        3. Track the character's emotional state and motivation
        4. Always respond in-character with deep consideration of their backstory and values
        
        When analyzing a situation, think about:
        - How would {character_data['name']} specifically react to this event?
        - What emotions would they feel?
        - What would their motivation or goal be in this situation?
        - What would they say or do next?
        
        Your output should be a JSON object with:
        - reasoning: Your step-by-step thought process about the character's reaction
        - action: A brief description of what the character does
        - dialogue: What the character says (if anything)
        - emotions: The character's current emotional state as key-value pairs
        - motivation: The character's current driving motivation
        """
    
    def _format_traits(self, traits: Dict[str, Any]) -> str:
        """Format character traits for the prompt"""
        return "\n".join([f"- {key}: {value}" for key, value in traits.items()])
    
    async def _format_input(self, input_data: Dict[str, Any]) -> List[HumanMessage]:
        """Format input data for character agent"""
        situation = input_data.get('situation', '')
        context = input_data.get('context', '')
        character_history = input_data.get('character_history', [])
        
        history_text = ""
        if character_history:
            history_text = "Recent character history:\n" + "\n".join([f"- {h}" for h in character_history[-5:]])
        
        message = f"""
        Current situation: {situation}
        
        Story context: {context}
        
        {history_text}
        
        How does {self.character_data['name']} react to this situation?
        """
        
        return [HumanMessage(content=message)]
    
    async def _process_response(self, response: str) -> Dict[str, Any]:
        """Process character agent response"""
        try:
            parser = JsonOutputParser(pydantic_object=CharacterResponse)
            parsed_response = parser.parse(response)
            return parsed_response
        except Exception as e:
            # Fallback for unparseable responses
            return {
                "reasoning": "Could not parse structured response",
                "action": "React to the situation",
                "dialogue": response.split('\n')[0] if '\n' in response else response[:100],
                "emotions": {"unknown": 1.0},
                "motivation": "Continue participation in the story"
            }