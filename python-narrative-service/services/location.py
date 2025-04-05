# services/location.py
from sqlmodel import Session, select
from models import Location, LocationChange, StorySection
from services.base import BaseService
from utils import db_operation_handler
from typing import List, Dict, Any, Optional
from datetime import datetime

class LocationService(BaseService[Location]):
    def __init__(self):
        super().__init__(Location)
    
    @db_operation_handler
    async def get_locations_by_story_id(self, db: Session, story_id: str) -> List[Location]:
        """Get all locations for a specific story"""
        return db.exec(
            select(Location)
            .where(Location.story_id == story_id)
        ).all()
    
    @db_operation_handler
    async def create_location(
        self, 
        db: Session, 
        story_id: str, 
        name: str, 
        description: str, 
        attributes: Dict[str, Any] = None
    ) -> Location:
        """Create a new location for a story"""
        location = Location(
            story_id=story_id,
            name=name,
            description=description,
            attributes=attributes or {}
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location
    
    @db_operation_handler
    async def update_location_attributes(
        self, 
        db: Session, 
        location_id: str, 
        section_id: str,
        change_description: str,
        new_attributes: Dict[str, Any]
    ) -> Location:
        """Update a location's attributes and record the change"""
        location = await self.get_by_id(db, location_id)
        if not location:
            raise ValueError(f"Location with ID {location_id} not found")
        
        # Store previous attributes for the change record
        previous_attributes = location.attributes.copy()
        
        # Update the attributes
        for key, value in new_attributes.items():
            location.attributes[key] = value
        
        location.updated_at = datetime.utcnow()
        
        # Record the change
        change = LocationChange(
            location_id=location_id,
            section_id=section_id,
            change_description=change_description,
            previous_attributes=previous_attributes,
            new_attributes=location.attributes
        )
        
        db.add(change)
        db.add(location)
        db.commit()
        db.refresh(location)
        
        return location
    
    @db_operation_handler
    async def get_location_history(
        self,
        db: Session,
        location_id: str
    ) -> List[Dict[str, Any]]:
        """Get the history of changes for a location"""
        location = await self.get_by_id(db, location_id)
        if not location:
            raise ValueError(f"Location with ID {location_id} not found")
        
        # Query the changes and join with story sections to get context
        changes = db.exec(
            select(LocationChange, StorySection)
            .join(StorySection, LocationChange.section_id == StorySection.id)
            .where(LocationChange.location_id == location_id)
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
                "previous_attributes": change.previous_attributes,
                "new_attributes": change.new_attributes,
                "created_at": change.created_at
            })
        
        return history