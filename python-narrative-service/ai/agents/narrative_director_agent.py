# ai/agents/narrative_director_agent.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from ai.agents.base_agent import BaseAgent, AgentOutput
from langchain_core.output_parsers import JsonOutputParser

class NarrativeOption(BaseModel):
    """Structure for a potential narrative direction"""
    description: str = Field(description="Description of the narrative option")
    impact_rating: float = Field(description="Impact on the story (0-10)")
    tension_change: float = Field(description="How this affects dramatic tension (-5 to +5)")

class NarrativeDirectorResponse(AgentOutput):
    """Output schema for the Narrative Director Agent"""
    narrative_options: List[NarrativeOption] = Field(description="Potential narrative directions")
    selected_direction: str = Field(description="The chosen narrative direction")
    pacing_assessment: str = Field(description="Assessment of current story pacing")
    tension_level: float = Field(description="Current tension level (0-10)")
    
class NarrativeDirectorAgent(BaseAgent):
    """Agent responsible for maintaining narrative structure and pacing"""
    
    def __init__(self, llm, story_id: str, story_data: Dict[str, Any]):
        """
        Initialize a narrative director agent
        
        Args:
            llm: The language model to use
            story_id: Database ID of the story
            story_data: Data about the story including genre, theme, etc.
        """
        super().__init__(
            llm=llm,
            agent_name="Narrative Director Agent",
            agent_description="An agent that manages story structure, pacing, and dramatic tension"
        )
        self.story_id = story_id
        self.story_data = story_data
        
        # Enhanced system prompt for narrative director agent
        self.system_prompt.content = f"""You are {self.agent_name}, {self.agent_description}.
        
        Story Details:
        - Genre: {story_data.get('genre', 'science fiction')}
        - Theme: {story_data.get('theme', '')}
        - Setting: {story_data.get('setting', '')}
        
        Your job is to:
        1. Monitor and manage the overall narrative arc of the story
        2. Ensure appropriate pacing, balancing action, dialogue, and exposition
        3. Maintain and adjust dramatic tension throughout the story
        4. Guide the story toward narratively satisfying developments
        5. Balance user agency with coherent narrative structure
        
        When directing the narrative, consider:
        - Where is the story in the traditional narrative arc? (exposition, rising action, climax, etc.)
        - Is the pacing too fast or too slow for this point in the story?
        - Is there appropriate build-up and release of tension?
        - Are characters being given meaningful challenges and growth opportunities?
        - How can user choices be incorporated while maintaining narrative cohesion?
        
        Your output should be a JSON object with:
        - reasoning: Your step-by-step thought process about narrative direction
        - action: The action you're taking (e.g. "Introducing conflict")
        - narrative_options: Potential directions the narrative could take
        - selected_direction: The narrative direction you're recommending
        - pacing_assessment: Your assessment of the current pacing
        - tension_level: The current level of dramatic tension (0-10)
        """
    
    async def _format_input(self, input_data: Dict[str, Any]) -> List[HumanMessage]:
        """Format input data for narrative director agent"""
        story_so_far = input_data.get('story_so_far', '')
        current_situation = input_data.get('current_situation', '')
        user_input = input_data.get('user_input', '')
        section_count = input_data.get('section_count', 0)
        
        message = f"""
        Story progression: Section {section_count} of the narrative
        
        Recent story context: {story_so_far[-1000:] if len(story_so_far) > 1000 else story_so_far}
        
        Current situation: {current_situation}
        
        User input/choice: {user_input}
        
        Provide narrative direction for the next part of the story.
        """
        
        return [HumanMessage(content=message)]
    
    async def _process_response(self, response: str) -> Dict[str, Any]:
        """Process narrative director agent response"""
        try:
            parser = JsonOutputParser(pydantic_object=NarrativeDirectorResponse)
            parsed_response = parser.parse(response)
            return parsed_response
        except Exception as e:
            # Fallback for unparseable responses
            return {
                "reasoning": "Could not parse structured response",
                "action": "Direct narrative",
                "narrative_options": [
                    {"description": "Continue current storyline", "impact_rating": 5.0, "tension_change": 0.0}
                ],
                "selected_direction": "Continue with the current narrative thread",
                "pacing_assessment": "Maintain current pacing",
                "tension_level": 5.0  # Medium tension as default
            }