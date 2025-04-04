# services/story_section.py
from sqlmodel import Session, select
from models import StorySection
from services.base import BaseService
from utils import db_operation_handler
from typing import List
from ai import ai_service

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
        story_service
    ) -> StorySection:
        """Add a new AI-generated continuation to a story based on user input"""
        # Get story context for AI
        story_context = await story_service.get_story_context(db, story_id)
        
        # Generate continuation with AI
        continuation_text = await ai_service.generate_story_continuation(
            story_context=story_context,
            user_input=user_input
        )
        
        # Find the highest order
        sections = await self.get_sections_by_story_id(db, story_id)
        next_order = max([s.order for s in sections], default=0) + 1
        
        # Create new section
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
        story_id: str,
        story_service
    ) -> List[str]:
        """Generate suggestions for what the user might do next"""
        # Get story context for AI
        story_context = await story_service.get_story_context(db, story_id)
        
        # Generate suggestions with AI
        suggestions = await ai_service.generate_story_suggestions(story_context)
        
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