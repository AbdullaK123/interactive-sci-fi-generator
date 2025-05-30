# ai/agents/orchestrator.py
from typing import Dict, Any, List, Optional
from ai.agents.character_agent import CharacterAgent
from ai.agents.world_state_agent import WorldStateAgent
from ai.agents.memory_curator_agent import MemoryCuratorAgent
from ai.agents.narrative_director_agent import NarrativeDirectorAgent
from sqlmodel import Session, select
from models import Story, StorySection, Character
from ai.monitoring import track_agent_operation
from ai.error_handling import agent_error_handler, memory_curator_fallback, narrative_director_fallback
from ai.error_handling import world_state_fallback, story_continuation_fallback, story_suggestions_fallback
from ai.config import get_agent_config
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

# Configure logging
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Coordinates the activities of multiple agents to generate narrative"""
    
    def __init__(self, llm, story_id: str, db: Session):
        """
        Initialize the agent orchestrator
        
        Args:
            llm: The language model to use
            story_id: Database ID of the story
            db: Database session
        """
        self.llm = llm
        self.story_id = story_id
        self.db = db
        
        # Initialize agents after loading story data
        self.story_data = None
        self.character_agents = {}
        self.world_state_agent = None
        self.memory_curator_agent = None
        self.narrative_director_agent = None
        self.initialized = False
    
    @track_agent_operation("orchestrator_initialize")
    async def initialize(self) -> bool:
        """Initialize the orchestrator and load all required data"""
        # Load story data
        self.story_data = await self._get_story_data()
        if not self.story_data:
            logger.error(f"Story with ID {self.story_id} not found")
            return False
        
        # Initialize narrative director agent
        self.narrative_director_agent = NarrativeDirectorAgent(
            llm=self.llm,
            story_id=self.story_id,
            story_data={
                "genre": self.story_data.genre,
                "theme": self.story_data.theme,
                "setting": self.story_data.setting
            }
        )
        
        # Initialize world state agent
        self.world_state_agent = WorldStateAgent(
            llm=self.llm,
            story_id=self.story_id,
            world_data={
                "genre": self.story_data.genre,
                "setting": self.story_data.setting,
                "rules": {}  # We'll populate this with world rules later
            }
        )
        
        # Initialize memory curator agent
        self.memory_curator_agent = MemoryCuratorAgent(
            llm=self.llm,
            story_id=self.story_id
        )
        
        # Load characters and initialize character agents
        await self._initialize_character_agents()
        
        self.initialized = True
        logger.info(f"Successfully initialized orchestrator for story {self.story_id}")
        return True
    
    async def _get_story_data(self) -> Optional[Story]:
        """Get story data from the database"""
        # Get story by ID
        story = self.db.exec(
            select(Story).where(Story.id == self.story_id)
        ).first()
        
        if not story:
            logger.error(f"Story with ID {self.story_id} not found")
            return None
        
        # Load story sections
        sections = self.db.exec(
            select(StorySection)
            .where(StorySection.story_id == self.story_id)
            .order_by(StorySection.order)
        ).all()
        
        # Attach sections to story
        story.sections = sections
        return story
    
    async def _initialize_character_agents(self):
        """Initialize character agents for all characters in the story"""
        # Get characters for the story
        characters = self.db.exec(
            select(Character).where(Character.story_id == self.story_id)
        ).all()
        
        # Create character agents
        for character in characters:
            self.character_agents[character.id] = CharacterAgent(
                llm=self.llm,
                character_id=character.id,
                character_data={
                    "name": character.name,
                    "description": character.description,
                    "traits": character.traits
                }
            )
        
        # If no characters exist yet, we'll create them later as the story progresses
        if not characters:
            logger.info(f"No characters found for story {self.story_id}. Will create as needed.")
    
    async def _ensure_initialized(self) -> bool:
        """Ensure the orchestrator is initialized"""
        if not self.initialized:
            logger.info(f"Orchestrator not initialized for story {self.story_id}. Initializing now...")
            return await self.initialize()
        return True
    
    @track_agent_operation("get_relevant_memories")
    @agent_error_handler(fallback_factory=memory_curator_fallback)
    async def _get_relevant_memories(self, current_situation: str, active_character_ids: List[str]):
        """Get relevant memories using the Memory Curator agent"""
        if not await self._ensure_initialized():
            logger.error("Cannot get relevant memories: orchestrator not initialized")
            return {"selected_memories": [], "relevance_reasoning": "Failed to initialize orchestrator"}
        
        # Get available memories from the database (events, character changes, etc.)
        from services.event import EventService
        event_service = EventService()
        story_events = await event_service.get_events_by_story_id(self.db, self.story_id)
        
        available_memories = []
        for event in story_events:
            participants = await event_service.get_event_participants(self.db, event.id)
            available_memories.append({
                "id": event.id,
                "time": event.created_at.isoformat(),
                "description": event.description,
                "importance": event.importance,
                "participants": [p["character_id"] for p in participants]
            })
        
        # Get active characters
        active_characters = []
        from services.character import CharacterService
        character_service = CharacterService()
        
        for character_id in active_character_ids:
            character = await character_service.get_by_id(self.db, character_id)
            if character:
                active_characters.append({
                    "id": character.id,
                    "name": character.name
                })
        
        # Use memory curator to select relevant memories
        memory_output = await self.memory_curator_agent.run({
            "current_situation": current_situation,
            "available_memories": available_memories,
            "active_characters": active_characters
        })
        
        return memory_output
    
    @track_agent_operation("get_character_reactions")
    async def _get_character_reactions(self, character_ids: List[str], situation: str, context: str):
        """Get reactions from specified characters"""
        if not await self._ensure_initialized():
            logger.error("Cannot get character reactions: orchestrator not initialized")
            return {}
        
        character_reactions = {}
        from services.character import CharacterService
        character_service = CharacterService()
        
        for character_id in character_ids:
            if character_id in self.character_agents:
                agent = self.character_agents[character_id]
                
                # Get character history
                character_history = []
                try:
                    character_changes = await character_service.get_character_history(self.db, character_id)
                    for change in character_changes[-10:]:  # Last 10
                        character_history.append(change["change_description"])
                except Exception:
                    logger.warning(f"Could not retrieve history for character {character_id}")
                
                # Get character reaction
                reaction = await agent.run({
                    "situation": situation,
                    "context": context,
                    "character_history": character_history
                })
                
                character_reactions[character_id] = reaction
        
        return character_reactions
    
    @track_agent_operation("check_world_consistency")
    @agent_error_handler(fallback_factory=world_state_fallback)
    async def _check_world_consistency(self, proposed_event: str, location_id: str = None):
        """Check world consistency using World State agent"""
        if not await self._ensure_initialized():
            logger.error("Cannot check world consistency: orchestrator not initialized")
            return {
                "world_effects": ["Error: orchestrator not initialized"],
                "consistency_issues": ["Error: orchestrator not initialized"],
                "physics_allowed": True  # Default to allowing actions
            }
        
        # Get location data if provided
        current_location = {}
        if location_id:
            from services.location import LocationService
            location_service = LocationService()
            location = await location_service.get_by_id(self.db, location_id)
            
            if location:
                current_location = {
                    "name": location.name,
                    "description": location.description,
                    "attributes": location.attributes
                }
        
        # Get recent world changes
        world_history = []
        from services.location import LocationService
        location_service = LocationService()
        
        locations = await location_service.get_locations_by_story_id(self.db, self.story_id)
        for location in locations:
            location_changes = await location_service.get_location_history(self.db, location.id)
            for change in location_changes[-5:]:  # Last 5 changes
                world_history.append(change["change_description"])
        
        # Check world consistency
        consistency_output = await self.world_state_agent.run({
            "proposed_event": proposed_event,
            "current_location": current_location,
            "world_history": world_history
        })
        
        return consistency_output
    
    @track_agent_operation("get_narrative_direction")
    @agent_error_handler(fallback_factory=narrative_director_fallback)
    async def _get_narrative_direction(self, user_input: str):
        """Get narrative direction using Narrative Director agent"""
        if not await self._ensure_initialized():
            logger.error("Cannot get narrative direction: orchestrator not initialized")
            return {
                "selected_direction": "Continue with the current narrative thread",
                "pacing_assessment": "Maintain current pacing",
                "tension_level": 5.0  # Medium tension as default
            }
        
        # Refresh story data to ensure we have the latest sections
        self.story_data = await self._get_story_data()
        
        # Get story so far
        story_sections = self.story_data.sections if self.story_data else []
        story_so_far = "\n".join([section.text for section in story_sections])
        
        # Get narrative direction
        direction_output = await self.narrative_director_agent.run({
            "story_so_far": story_so_far,
            "current_situation": story_sections[-1].text if story_sections else "",
            "user_input": user_input,
            "section_count": len(story_sections)
        })
        
        return direction_output
    
    @track_agent_operation("generate_story_continuation")
    @agent_error_handler(fallback_factory=story_continuation_fallback)
    async def generate_story_continuation(self, user_input: str, active_characters: List[str] = None):
        """
        Generate story continuation using all agents
        
        Args:
            user_input: User's input/choice
            active_characters: IDs of active characters (if known)
            
        Returns:
            Generated continuation text
        """
        logger.info(f"Generating story continuation for story {self.story_id}")
        
        # Ensure orchestrator is initialized
        if not await self._ensure_initialized():
            logger.error(f"Cannot generate continuation: orchestrator not initialized")
            return self._generate_fallback_response(user_input)
        
        # If no active characters specified, create default characters if there are none
        if not active_characters:
            # Check if we have characters in the database
            from services.character import CharacterService
            character_service = CharacterService()
            characters = await character_service.get_characters_by_story_id(self.db, self.story_id)
            
            if not characters:
                # Create a default character if none exist
                default_character = await character_service.create_character(
                    self.db,
                    self.story_id,
                    "Protagonist",
                    "The main character of the story, a rebellious figure in a dystopian world.",
                    {"courage": 0.8, "intelligence": 0.7, "determination": 0.9},
                    1.0
                )
                active_characters = [default_character.id]
            else:
                active_characters = [character.id for character in characters]
        
        # 1. Get narrative direction
        narrative_direction = await self._get_narrative_direction(user_input)
        
        # 2. Check world consistency for proposed direction
        world_consistency = await self._check_world_consistency(
            proposed_event=narrative_direction.get("selected_direction", user_input)
        )
        
        # 3. Get relevant memories
        memory_output = await self._get_relevant_memories(
            current_situation=user_input,
            active_character_ids=active_characters
        )
        
        # 4. Get character reactions
        character_reactions = await self._get_character_reactions(
            character_ids=active_characters,
            situation=user_input,
            context=narrative_direction.get("selected_direction", "Continue the story")
        )
        
        # 5. Compile all agent outputs to craft final narrative
        narrative_context = {
            "user_input": user_input,
            "narrative_direction": narrative_direction,
            "world_consistency": world_consistency,
            "memories": memory_output,
            "character_reactions": character_reactions
        }
        
        # 6. Use a narrative generation prompt to combine agent outputs
        system_template = """You are a skilled narrative writer specializing in {genre} fiction.
        Your task is to craft the next segment of an interactive story based on the user's input
        and the guidance provided by various narrative agents.
        
        Story Theme: {theme}
        Story Setting: {setting}
        
        Write 2-3 paragraphs continuing the story based on the user's input. 
        Incorporate character reactions, maintain world consistency, and follow the suggested narrative direction.
        
        Write in the second person perspective (using "you").
        The text should be engaging, descriptive, and end with a situation that invites further action.
        """
        
        human_template = """
        USER'S CHOICE:
        {user_input}
        
        NARRATIVE DIRECTION:
        {narrative_direction}
        
        WORLD CONSISTENCY CHECK:
        {world_consistency}
        
        RELEVANT MEMORIES:
        {memories}
        
        CHARACTER REACTIONS:
        {character_reactions}
        
        Continue the story based on this information.
        """
        
        # Format all the inputs for the narrative generation prompt
        narrative_direction_text = f"""
        Selected Direction: {narrative_direction.get('selected_direction', 'Continue the story')}
        Pacing: {narrative_direction.get('pacing_assessment', 'Normal pacing')}
        Tension Level: {narrative_direction.get('tension_level', 5.0)}
        """
        
        world_consistency_text = f"""
        Physically Allowed: {world_consistency.get('physics_allowed', True)}
        World Effects: {', '.join(world_consistency.get('world_effects', ['No significant effects']))}
        Issues to Address: {', '.join(world_consistency.get('consistency_issues', [])) or 'None'}
        """
        
        # Format memory information
        memory_text = ""
        if 'selected_memories' in memory_output and memory_output['selected_memories']:
            memory_text = "\n".join([
                f"- {memory.get('description', '')} (Relevance: {memory.get('relevance_score', 0)})"
                for memory in memory_output['selected_memories']
            ])
        else:
            memory_text = "No specific memories relevant to current situation."
        
        # Format character reactions
        character_reaction_text = ""
        for character_id, reaction in character_reactions.items():
            from services.character import CharacterService
            character_service = CharacterService()
            character = await character_service.get_by_id(self.db, character_id)
            
            if character:
                character_reaction_text += f"\n{character.name}:\n"
                character_reaction_text += f"- Action: {reaction.get('action', '')}\n"
                if 'dialogue' in reaction and reaction['dialogue']:
                    character_reaction_text += f"- Dialogue: \"{reaction['dialogue']}\"\n"
                if 'emotions' in reaction and reaction['emotions']:
                    emotions_str = ", ".join([f"{k}: {v}" for k, v in reaction['emotions'].items()])
                    character_reaction_text += f"- Emotions: {emotions_str}\n"
        
        if not character_reaction_text:
            character_reaction_text = "No specific character reactions available."
        
        # Create the chat prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
        # Create the chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Generate the continuation
        continuation = await chain.ainvoke({
            "genre": self.story_data.genre,
            "theme": self.story_data.theme,
            "setting": self.story_data.setting or "",
            "user_input": user_input,
            "narrative_direction": narrative_direction_text,
            "world_consistency": world_consistency_text,
            "memories": memory_text,
            "character_reactions": character_reaction_text
        })
        
        # 7. Store the generated text and update the story state
        await self._update_story_state(continuation, narrative_context)
        
        return continuation
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Generate a fallback response when the agent system fails"""
        # Basic fallback that at least acknowledges the user's input
        genre = getattr(self.story_data, 'genre', 'science fiction') if self.story_data else 'science fiction'
        theme = getattr(self.story_data, 'theme', 'exploration') if self.story_data else 'exploration'
        
        return f"""
            You decide to {user_input.lower() if not user_input.lower().startswith('i ') else user_input[2:].lower()}.
                    
            The {genre} world around you responds to your actions. As you continue on your journey of {theme}, you notice new details about your surroundings.

            What will you do next?
        """
    
    async def _update_story_state(self, continuation_text: str, narrative_context: Dict[str, Any]):
        """
        Update the story state based on the generated continuation
        
        Args:
            continuation_text: The generated story continuation
            narrative_context: Context used to generate the continuation
        """
        # Update character states if we have character reactions
        if 'character_reactions' in narrative_context:
            from services.character import CharacterService
            character_service = CharacterService()
            
            for character_id, reaction in narrative_context['character_reactions'].items():
                if 'emotions' in reaction:
                    character = await character_service.get_by_id(self.db, character_id)
                    if character:
                        # Update character traits based on reactions
                        new_traits = character.traits.copy()
                        
                        # Add or update emotional state
                        if 'emotions' not in new_traits:
                            new_traits['emotions'] = {}
                        
                        for emotion, value in reaction['emotions'].items():
                            new_traits['emotions'][emotion] = value
                        
                        # Add motivation if available
                        if 'motivation' in reaction:
                            new_traits['current_motivation'] = reaction['motivation']
                        
                        # Get the latest story section for reference
                        latest_section = self.story_data.sections[-1] if self.story_data.sections else None
                        
                        if latest_section:
                            await character_service.update_character_traits(
                                self.db,
                                character_id,
                                latest_section.id,
                                f"Character state updated after {narrative_context['user_input']}",
                                new_traits
                            )
    
    @track_agent_operation("generate_story_suggestions")
    @agent_error_handler(fallback_factory=story_suggestions_fallback)
    async def generate_story_suggestions(self) -> List[str]:
        """Generate suggestions for what the user might do next"""
        logger.info(f"Generating story suggestions for story {self.story_id}")
        
        # Ensure orchestrator is initialized
        if not await self._ensure_initialized():
            logger.error(f"Cannot generate suggestions: orchestrator not initialized")
            return ["Explore your surroundings", "Talk to someone nearby", "Look for clues"]
        
        # Refresh story data to ensure we have the latest sections
        self.story_data = await self._get_story_data()
        
        # Get the latest story section for context
        latest_section = self.story_data.sections[-1] if self.story_data and self.story_data.sections else None
        
        if not latest_section:
            return ["Begin your adventure", "Explore your surroundings", "Talk to someone nearby"]
        
        # Use the narrative director to generate suggestions
        direction_output = await self.narrative_director_agent.run({
            "story_so_far": "\n".join([section.text for section in self.story_data.sections]),
            "current_situation": latest_section.text,
            "user_input": "",
            "section_count": len(self.story_data.sections)
        })
        
        # Extract possible narrative directions
        suggestions = []
        if 'narrative_options' in direction_output and direction_output['narrative_options']:
            for option in direction_output['narrative_options']:
                if len(suggestions) < 3 and 'description' in option:
                    # Convert narrative option to an actionable suggestion
                    action = self._convert_to_action(option['description'])
                    suggestions.append(action)
        
        # Ensure we have at least 3 suggestions
        while len(suggestions) < 3:
            suggestions.append(self._generate_generic_suggestion(len(suggestions)))
        
        return suggestions[:3]  # Return at most 3 suggestions
    
    def _convert_to_action(self, narrative_option: str) -> str:
        """Convert a narrative option to an actionable suggestion"""
        # This is a simple implementation - could be enhanced with NLP
        # Strip any leading articles or pronouns
        action = narrative_option.strip()
        
        for prefix in ["The character should ", "You should ", "The protagonist should "]:
            if action.startswith(prefix):
                action = action[len(prefix):]
        
        # Ensure it starts with a verb
        if not any(action.lower().startswith(verb) for verb in [
            "go", "look", "search", "talk", "ask", "find", "use", "take", "open", 
            "examine", "investigate", "explore", "approach", "run", "hide", "fight"
        ]):
            verbs = ["Explore", "Investigate", "Check out", "Look for", "Talk to", "Search"]
            import random
            action = f"{random.choice(verbs)} {action}"
        
        return action.strip()
    
    def _generate_generic_suggestion(self, index: int) -> str:
        """Generate a generic suggestion based on index"""
        suggestions = [
            "Explore your surroundings",
            "Talk to someone nearby",
            "Look for clues or useful items",
            "Try a different approach",
            "Think about what you've learned so far"
        ]
        
        if index < len(suggestions):
            return suggestions[index]
        else:
            return suggestions[-1]