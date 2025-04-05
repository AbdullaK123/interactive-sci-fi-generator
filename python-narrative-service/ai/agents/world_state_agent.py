# ai/agents/world_state_agent.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from ai.agents.base_agent import BaseAgent, AgentOutput
from langchain_core.output_parsers import JsonOutputParser


class WorldStateResponse(AgentOutput):
    """Output schema for the World State Agent"""
    world_effects: List[str] = Field(description="Effects on the world state")
    consistency_issues: List[str] = Field(default_factory=list, description="Potential consistency issues")
    physics_allowed: bool = Field(description="Whether the action is physically possible in this world")
    
class WorldStateAgent(BaseAgent):
    """Agent responsible for maintaining world consistency and physics"""
    
    def __init__(self, llm, story_id: str, world_data: Dict[str, Any]):
        """
        Initialize a world state agent
        
        Args:
            llm: The language model to use
            story_id: Database ID of the story
            world_data: World data including setting, rules, etc.
        """
        super().__init__(
            llm=llm,
            agent_name="World State Agent",
            agent_description="An agent that maintains consistency of the fictional world's rules, physics, and environment"
        )
        self.story_id = story_id
        self.world_data = world_data
        
        # Enhanced system prompt for world state agent
        self.system_prompt.content = f"""You are {self.agent_name}, {self.agent_description}.
        
        World Details:
        - Genre: {world_data.get('genre', 'science fiction')}
        - Setting: {world_data.get('setting', '')}
        
        World Rules:
        {self._format_world_rules(world_data.get('rules', {}))}
        
        Your job is to:
        1. Enforce consistency in the fictional world's rules, physics, and environment
        2. Evaluate whether proposed events are physically possible within the established rules
        3. Identify any consistency issues in new narrative developments
        4. Track changes to the physical state of the world, locations, and objects
        
        When analyzing a situation, think about:
        - Is this physically possible in this world?
        - What effects would this have on the physical environment?
        - Does this contradict any established world rules or previously established facts?
        - What physical consequences would logically follow from these actions?
        
        Your output should be a JSON object with:
        - reasoning: Your step-by-step thought process about world consistency
        - action: The action you're taking (e.g. "Enforcing physics rules")
        - world_effects: A list of effects on the world state
        - consistency_issues: Any potential consistency issues identified
        - physics_allowed: Boolean indicating if the action is physically possible
        """
    
    def _format_world_rules(self, rules: Dict[str, Any]) -> str:
        """Format world rules for the prompt"""
        return "\n".join([f"- {key}: {value}" for key, value in rules.items()])
    
    async def _format_input(self, input_data: Dict[str, Any]) -> List[HumanMessage]:
        """Format input data for world state agent"""
        proposed_event = input_data.get('proposed_event', '')
        current_location = input_data.get('current_location', {})
        world_history = input_data.get('world_history', [])
        
        history_text = ""
        if world_history:
            history_text = "Recent world changes:\n" + "\n".join([f"- {h}" for h in world_history[-5:]])
        
        location_text = ""
        if current_location:
            location_text = f"""
            Current location: {current_location.get('name', '')}
            Location description: {current_location.get('description', '')}
            Location attributes: {', '.join([f"{k}: {v}" for k, v in current_location.get('attributes', {}).items()])}
            """
        
        message = f"""
        Proposed event: {proposed_event}
        
        {location_text}
        
        {history_text}
        
        Analyze this event for world consistency and physical possibility.
        """
        
        return [HumanMessage(content=message)]
    
    async def _process_response(self, response: str) -> Dict[str, Any]:
        """Process world state agent response"""
        try:
            parser = JsonOutputParser(pydantic_object=WorldStateResponse)
            parsed_response = parser.parse(response)
            return parsed_response
        except Exception as e:
            # Fallback for unparseable responses
            return {
                "reasoning": "Could not parse structured response",
                "action": "Evaluate world consistency",
                "world_effects": ["Unknown effects on the world"],
                "consistency_issues": [],
                "physics_allowed": True  # Default to allowing actions when parsing fails
            }