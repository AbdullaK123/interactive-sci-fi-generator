# services/event.py
from sqlmodel import Session, select
from models import Event, EventParticipant, Character
from services.base import BaseService
from utils import db_operation_handler
from typing import List, Dict, Any, Optional
from datetime import datetime

class EventService(BaseService[Event]):
    def __init__(self):
        super().__init__(Event)
    
    @db_operation_handler
    async def get_events_by_story_id(
        self,
        db: Session,
        story_id: str,
        min_importance: float = 0.0
    ) -> List[Event]:
        """Get all events for a specific story, optionally filtered by importance"""
        return db.exec(
            select(Event)
            .where(Event.story_id == story_id)
            .where(Event.importance >= min_importance)
            .order_by(Event.created_at)
        ).all()
    
    @db_operation_handler
    async def get_events_by_section_id(
        self,
        db: Session,
        section_id: str
    ) -> List[Event]:
        """Get all events for a specific story section"""
        return db.exec(
            select(Event)
            .where(Event.section_id == section_id)
            .order_by(Event.importance.desc())
        ).all()
    
    @db_operation_handler
    async def get_events_by_location_id(
        self,
        db: Session,
        location_id: str
    ) -> List[Event]:
        """Get all events that occurred at a specific location"""
        return db.exec(
            select(Event)
            .where(Event.location_id == location_id)
            .order_by(Event.created_at)
        ).all()
    
    @db_operation_handler
    async def get_events_by_character_id(
        self,
        db: Session,
        character_id: str
    ) -> List[Dict[str, Any]]:
        """Get all events that a character participated in"""
        # Query events and participation roles for a character
        results = db.exec(
            select(Event, EventParticipant)
            .join(EventParticipant, Event.id == EventParticipant.event_id)
            .where(EventParticipant.character_id == character_id)
            .order_by(Event.created_at)
        ).all()
        
        # Format the results
        events = []
        for event, participant in results:
            events.append({
                "event_id": event.id,
                "title": event.title,
                "description": event.description,
                "importance": event.importance,
                "role": participant.role,
                "created_at": event.created_at
            })
        
        return events
    
    @db_operation_handler
    async def create_event(
        self,
        db: Session,
        story_id: str,
        section_id: str,
        title: str,
        description: str,
        importance: float = 1.0,
        location_id: Optional[str] = None,
        attributes: Dict[str, Any] = None
    ) -> Event:
        """Create a new event"""
        event = Event(
            story_id=story_id,
            section_id=section_id,
            title=title,
            description=description,
            importance=importance,
            location_id=location_id,
            attributes=attributes or {}
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
    
    @db_operation_handler
    async def add_character_to_event(
        self,
        db: Session,
        event_id: str,
        character_id: str,
        role: str
    ) -> EventParticipant:
        """Add a character as a participant in an event"""
        # Verify the event and character exist
        event = await self.get_by_id(db, event_id)
        if not event:
            raise ValueError(f"Event with ID {event_id} not found")
            
        character = db.exec(select(Character).where(Character.id == character_id)).first()
        if not character:
            raise ValueError(f"Character with ID {character_id} not found")
        
        # Check if the character is already a participant
        existing = db.exec(
            select(EventParticipant)
            .where(EventParticipant.event_id == event_id)
            .where(EventParticipant.character_id == character_id)
        ).first()
        
        if existing:
            # Update the role if it already exists
            existing.role = role
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create a new participant entry
        participant = EventParticipant(
            event_id=event_id,
            character_id=character_id,
            role=role
        )
        
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        return participant
    
    @db_operation_handler
    async def get_event_participants(
        self,
        db: Session,
        event_id: str
    ) -> List[Dict[str, Any]]:
        """Get all characters that participated in an event with their roles"""
        # Query participants and join with characters to get their details
        results = db.exec(
            select(EventParticipant, Character)
            .join(Character, EventParticipant.character_id == Character.id)
            .where(EventParticipant.event_id == event_id)
        ).all()
        
        participants = []
        for participant, character in results:
            participants.append({
                "participant_id": participant.id,
                "character_id": character.id,
                "character_name": character.name,
                "role": participant.role
            })
        
        return participants