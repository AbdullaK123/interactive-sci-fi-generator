# python-narrative-service/services/agent_service.py
from typing import Dict, Any, List, Optional
from sqlmodel import Session
from ai.agents.orchestrator import AgentOrchestrator
from models import Story, StorySection
from ai import ai_service
import logging
from utils import db_operation_handler

logger = logging.getLogger(__name__)

class AgentService:
    """Service for integrating AI agents with the API endpoints"""
    
    def __init__(self):
        self._orchestrators = {}  # Cache for story orchestrators
    
    async def _get_orchestrator(self, db: Session, story_id: str) -> AgentOrchestrator:
        """Get (or create) an orchestrator for the given story"""
        if story_id in self._orchestrators:
            return self._orchestrators[story_id]
        
        # Create a new orchestrator
        llm = ai_service.llm
        orchestrator = AgentOrchestrator(llm, story_id, db)
        await orchestrator.initialize()
        
        # Cache the orchestrator
        self._orchestrators[story_id] = orchestrator
        
        return orchestrator
    
    @db_operation_handler
    async def generate_continuation(
        self, 
        db: Session, 
        story_id: str, 
        user_input: str
    ) -> StorySection:
        """Generate a story continuation using the agent system"""
        # Get the orchestrator
        orchestrator = await self._get_orchestrator(db, story_id)
        
        # Generate the continuation
        continuation_text = await orchestrator.generate_story_continuation(user_input)
        
        # Find the highest order among existing sections
        from services import service_registry
        sections = await service_registry.get("story_section_service").get_sections_by_story_id(db, story_id)
        next_order = max([s.order for s in sections], default=0) + 1
        
        # Create a new section
        section = StorySection(
            story_id=story_id,
            text=continuation_text,
            order=next_order
        )
        
        db.add(section)
        db.commit()
        db.refresh(section)
        
        return section
    
    @db_operation_handler
    async def generate_suggestions(
        self,
        db: Session,
        story_id: str
    ) -> List[str]:
        """Generate suggestions for what the user might do next"""
        # Get the orchestrator
        orchestrator = await self._get_orchestrator(db, story_id)
        
        # Generate suggestions
        suggestions = await orchestrator.generate_story_suggestions()
        
        return suggestions
    
    @db_operation_handler
    async def analyze_user_input(
        self,
        db: Session,
        story_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """Analyze user input to extract intents, entities, etc."""
        # This would use the InputProcessor from earlier
        # For now, we'll return a simplified version
        
        return {
            "intent": "generic",
            "normalized_input": user_input,
            "feasibility": True
        }
    
    def clear_orchestrator_cache(self, story_id: Optional[str] = None):
        """Clear orchestrator cache for a story or all stories"""
        if story_id:
            if story_id in self._orchestrators:
                del self._orchestrators[story_id]
        else:
            self._orchestrators.clear()

# Create a singleton instance
agent_service = AgentService()