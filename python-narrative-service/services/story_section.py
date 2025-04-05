# services/story_section.py
from sqlmodel import Session, select
from models import StorySection
from services.base import BaseService
from utils import db_operation_handler
from typing import List
from services.agent_service import agent_service

class StorySectionService(BaseService[StorySection]):
    def __init__(self):
        super().__init__(StorySection)
    
    @db_operation_handler
    async def get_sections_by_story_id(self, db: Session, story_id: str) -> List[StorySection]:
        """Get all sections for a specific story"""
        return db.exec(
            select(StorySection)
            .where(StorySection.story_id == story_id)
            .order_by(StorySection.order)
        ).all()
    
    @db_operation_handler
    async def add_ai_continuation(
        self, 
        db: Session, 
        story_id: str, 
        user_input: str,
        story_service = None
    ) -> StorySection:
        """Add a new AI-generated continuation to a story based on user input"""
        # Use the agent service to generate the continuation
        section = await agent_service.generate_continuation(
            db,
            story_id,
            user_input
        )
        return section
    
    @db_operation_handler
    async def generate_suggestions(
        self,
        db: Session,
        story_id: str,
        story_service = None
    ) -> List[str]:
        """Generate suggestions for what the user might do next"""
        # Use the agent service to generate suggestions
        suggestions = await agent_service.generate_suggestions(
            db,
            story_id
        )
        return suggestions
    
    @db_operation_handler
    async def add_section_to_story(
        self, 
        db: Session, 
        story_id: str, 
        text: str
    ) -> StorySection:
        """Add a new section to a story"""
        # Find the highest order
        sections = await self.get_sections_by_story_id(db, story_id)
        next_order = max([s.order for s in sections], default=0) + 1
        
        # Create new section
        section = StorySection(
            story_id=story_id,
            text=text,
            order=next_order
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        
        return section