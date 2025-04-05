# services/character.py
from sqlmodel import Session, select
from models import Character, CharacterChange, StorySection
from services.base import BaseService
from utils import db_operation_handler
import datetime
from typing import List, Dict, Any, Optional

class CharacterService(BaseService[Character]):
    def __init__(self):
        super().__init__(Character)
    
    @db_operation_handler
    async def get_characters_by_story_id(self, db: Session, story_id: str) -> List[Character]:
        """Get all characters for a specific story"""
        return db.exec(
            select(Character)
            .where(Character.story_id == story_id)
        ).all()
    
    @db_operation_handler
    async def get_characters_by_importance(self, db: Session, story_id: str, min_importance: float = 0.0) -> List[Character]:
        """Get characters filtered by minimum importance level"""
        return db.exec(
            select(Character)
            .where(Character.story_id == story_id)
            .where(Character.importance >= min_importance)
            .order_by(Character.importance.desc())
        ).all()
    
    @db_operation_handler
    async def create_character(
        self, 
        db: Session, 
        story_id: str, 
        name: str, 
        description: str, 
        traits: Dict[str, Any] = None,
        importance: float = 1.0
    ) -> Character:
        """Create a new character for a story"""
        character = Character(
            story_id=story_id,
            name=name,
            description=description,
            traits=traits or {},
            importance=importance
        )
        db.add(character)
        db.commit()
        db.refresh(character)
        return character
    
    @db_operation_handler
    async def update_character_traits(
        self, 
        db: Session, 
        character_id: str, 
        section_id: str,
        change_description: str,
        new_traits: Dict[str, Any],
        include_description_update: bool = False
    ) -> Character:
        """Update a character's traits and record the change"""
        character = await self.get_by_id(db, character_id)
        if not character:
            raise ValueError(f"Character with ID {character_id} not found")
        
        # Store previous traits for the change record
        previous_traits = character.traits.copy()
        
        # Update the traits
        for key, value in new_traits.items():
            character.traits[key] = value
        
        character.updated_at = datetime.utcnow()
        
        # Record the change
        change = CharacterChange(
            character_id=character_id,
            section_id=section_id,
            change_description=change_description,
            previous_traits=previous_traits,
            new_traits=character.traits
        )
        
        db.add(change)
        db.add(character)
        db.commit()
        db.refresh(character)
        
        return character
    
    @db_operation_handler
    async def update_character_importance(
        self,
        db: Session,
        character_id: str,
        new_importance: float
    ) -> Character:
        """Update a character's importance score"""
        character = await self.get_by_id(db, character_id)
        if not character:
            raise ValueError(f"Character with ID {character_id} not found")
        
        character.importance = new_importance
        character.updated_at = datetime.utcnow()
        
        db.add(character)
        db.commit()
        db.refresh(character)
        
        return character
    
    @db_operation_handler
    async def get_character_history(
        self,
        db: Session,
        character_id: str
    ) -> List[Dict[str, Any]]:
        """Get the history of changes for a character"""
        character = await self.get_by_id(db, character_id)
        if not character:
            raise ValueError(f"Character with ID {character_id} not found")
        
        # Query the changes and join with story sections to get context
        changes = db.exec(
            select(CharacterChange, StorySection)
            .join(StorySection, CharacterChange.section_id == StorySection.id)
            .where(CharacterChange.character_id == character_id)
            .order_by(StorySection.order)
        ).all()
        
        # Format the history
        history = []
        for change, section in changes:
            history.append({
                "change_id": change.id,
                "section_id": section.id,
                "section_order": section.order,
                "change_description": change.change_description,
                "previous_traits": change.previous_traits,
                "new_traits": change.new_traits,
                "created_at": change.created_at
            })
        
        return history