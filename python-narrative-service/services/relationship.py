# services/relationship.py
from sqlmodel import Session, select
from models import EntityRelationship, RelationshipChange, StorySection, Character, RelationshipType
from services.base import BaseService
from utils import db_operation_handler
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

class RelationshipService(BaseService[EntityRelationship]):
    def __init__(self):
        super().__init__(EntityRelationship)
    
    @db_operation_handler
    async def get_character_relationships(
        self, 
        db: Session, 
        character_id: str
    ) -> List[EntityRelationship]:
        """Get all relationships where the character is source or target"""
        return db.exec(
            select(EntityRelationship)
            .where(
                (EntityRelationship.source_character_id == character_id) |
                (EntityRelationship.target_character_id == character_id)
            )
        ).all()
    
    @db_operation_handler
    async def get_relationship_between_characters(
        self,
        db: Session,
        character1_id: str,
        character2_id: str
    ) -> Optional[EntityRelationship]:
        """Get relationship between two specific characters if it exists"""
        relationship = db.exec(
            select(EntityRelationship)
            .where(
                (
                    (EntityRelationship.source_character_id == character1_id) & 
                    (EntityRelationship.target_character_id == character2_id)
                ) | 
                (
                    (EntityRelationship.source_character_id == character2_id) & 
                    (EntityRelationship.target_character_id == character1_id)
                )
            )
        ).first()
        
        return relationship
    
    @db_operation_handler
    async def create_relationship(
        self,
        db: Session,
        source_character_id: str,
        target_character_id: str,
        relationship_type: RelationshipType,
        strength: float = 1.0,
        attributes: Dict[str, Any] = None
    ) -> EntityRelationship:
        """Create a new relationship between characters"""
        # Verify that both characters exist
        source = db.exec(select(Character).where(Character.id == source_character_id)).first()
        target = db.exec(select(Character).where(Character.id == target_character_id)).first()
        
        if not source:
            raise ValueError(f"Source character with ID {source_character_id} not found")
        if not target:
            raise ValueError(f"Target character with ID {target_character_id} not found")
        
        # Check if relationship already exists
        existing = await self.get_relationship_between_characters(db, source_character_id, target_character_id)
        if existing:
            raise ValueError(f"Relationship already exists between characters {source_character_id} and {target_character_id}")
        
        # Create the relationship
        relationship = EntityRelationship(
            source_character_id=source_character_id,
            target_character_id=target_character_id,
            relationship_type=relationship_type,
            strength=strength,
            attributes=attributes or {}
        )
        
        db.add(relationship)
        db.commit()
        db.refresh(relationship)
        
        return relationship
    
    @db_operation_handler
    async def update_relationship(
        self,
        db: Session,
        relationship_id: str,
        section_id: str,
        change_description: str,
        new_type: Optional[RelationshipType] = None,
        new_strength: Optional[float] = None,
        new_attributes: Optional[Dict[str, Any]] = None
    ) -> EntityRelationship:
        """Update a relationship and record the change"""
        relationship = await self.get_by_id(db, relationship_id)
        if not relationship:
            raise ValueError(f"Relationship with ID {relationship_id} not found")
        
        # Store previous values
        previous_type = relationship.relationship_type
        previous_strength = relationship.strength
        previous_attributes = relationship.attributes.copy()
        
        # Update values if provided
        if new_type is not None:
            relationship.relationship_type = new_type
        
        if new_strength is not None:
            relationship.strength = new_strength
        
        if new_attributes is not None:
            for key, value in new_attributes.items():
                relationship.attributes[key] = value
        
        relationship.updated_at = datetime.utcnow()
        
        # Record the change
        change = RelationshipChange(
            relationship_id=relationship_id,
            section_id=section_id,
            change_description=change_description,
            previous_type=previous_type if new_type is not None else None,
            new_type=relationship.relationship_type if new_type is not None else None,
            previous_strength=previous_strength if new_strength is not None else None,
            new_strength=relationship.strength if new_strength is not None else None,
            previous_attributes=previous_attributes,
            new_attributes=relationship.attributes
        )
        
        db.add(change)
        db.add(relationship)
        db.commit()
        db.refresh(relationship)
        
        return relationship
    
    @db_operation_handler
    async def get_relationship_history(
        self,
        db: Session,
        relationship_id: str
    ) -> List[Dict[str, Any]]:
        """Get the history of changes for a relationship"""
        relationship = await self.get_by_id(db, relationship_id)
        if not relationship:
            raise ValueError(f"Relationship with ID {relationship_id} not found")
        
        # Query the changes and join with story sections to get context
        changes = db.exec(
            select(RelationshipChange, StorySection)
            .join(StorySection, RelationshipChange.section_id == StorySection.id)
            .where(RelationshipChange.relationship_id == relationship_id)
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
                "previous_type": change.previous_type,
                "new_type": change.new_type,
                "previous_strength": change.previous_strength,
                "new_strength": change.new_strength,
                "previous_attributes": change.previous_attributes,
                "new_attributes": change.new_attributes,
                "created_at": change.created_at
            })
        
        return history