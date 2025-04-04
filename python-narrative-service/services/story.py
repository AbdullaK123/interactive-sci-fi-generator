# services/story.py
from sqlmodel import Session, select
from models import Story, StoryCreate, StorySection
from services.base import BaseService
from utils import db_operation_handler
from typing import List, Dict, Any
from ai import ai_service

class StoryService(BaseService[Story]):
    def __init__(self):
        super().__init__(Story)
    
    @db_operation_handler
    async def create_with_ai_introduction(
        self, 
        db: Session, 
        story_data: StoryCreate
    ) -> Story:
        """Create a story with an AI-generated introduction"""
        # Create story
        story = await self.create(db, story_data)
        
        # Generate introduction with AI
        intro_text = await ai_service.generate_story_introduction(
            genre=story.genre,
            theme=story.theme,
            setting=story.setting or ""
        )
        
        # Create initial section
        section = StorySection(
            story_id=story.id,
            text=intro_text,
            order=1
        )
        db.add(section)
        db.commit()
        db.refresh(story)
        
        return story
    
    @db_operation_handler
    async def get_story_with_sections(self, db: Session, story_id: str) -> Story:
        """Get a story with all its sections"""
        story = await self.get_by_id(db, story_id)
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")
        return story
    
    @db_operation_handler
    async def get_story_context(self, db: Session, story_id: str) -> Dict[str, Any]:
        """Get context information needed for AI to generate continuations"""
        story = await self.get_story_with_sections(db, story_id)
        
        # Extract text from all sections
        section_texts = [section.text for section in story.sections]
        
        return {
            "genre": story.genre,
            "theme": story.theme,
            "setting": story.setting,
            "previous_sections": section_texts
        }