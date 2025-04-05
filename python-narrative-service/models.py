# Enhanced models.py

from typing import List, Optional, Dict, Any, ForwardRef
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from datetime import datetime
import uuid
from enum import Enum as PyEnum

# Helper function to generate UUIDs as strings (already in your code)
def generate_uuid():
    return str(uuid.uuid4())

# Enums
class StoryGenre(str, PyEnum):
    SCIFI = "scifi"
    CYBERPUNK = "cyberpunk"
    SPACE_OPERA = "space_opera"
    DYSTOPIAN = "dystopian"

class RelationshipType(str, PyEnum):
    FRIEND = "friend"
    ENEMY = "enemy"
    ALLY = "ally"
    RIVAL = "rival"
    FAMILY = "family"
    ROMANTIC = "romantic"
    PROFESSIONAL = "professional"
    UNKNOWN = "unknown"

# Your existing Story models
class StoryBase(SQLModel):
    genre: str = Field(...)
    theme: str = Field(...)
    setting: Optional[str] = Field(default=None)

class Story(StoryBase, table=True):
    __tablename__ = "stories"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    sections: List["StorySection"] = Relationship(back_populates="story")
    characters: List["Character"] = Relationship(back_populates="story")
    locations: List["Location"] = Relationship(back_populates="story")
    events: List["Event"] = Relationship(back_populates="story")

# Character model
class CharacterBase(SQLModel):
    name: str = Field(...)
    description: str = Field(...)
    traits: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    importance: float = Field(default=1.0)  # 1-10 scale for story importance

class Character(CharacterBase, table=True):
    __tablename__ = "characters"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(foreign_key="stories.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    story: Story = Relationship(back_populates="characters")
    character_changes: List["CharacterChange"] = Relationship(back_populates="character")
    relationships_as_source: List["EntityRelationship"] = Relationship(
        back_populates="source_character",
        sa_relationship_kwargs={"foreign_keys": "EntityRelationship.source_character_id"}
    )
    relationships_as_target: List["EntityRelationship"] = Relationship(
        back_populates="target_character",
        sa_relationship_kwargs={"foreign_keys": "EntityRelationship.target_character_id"}
    )
    event_participants: List["EventParticipant"] = Relationship(back_populates="character")

class CharacterChange(SQLModel, table=True):
    __tablename__ = "character_changes"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    character_id: str = Field(foreign_key="characters.id")
    section_id: str = Field(foreign_key="story_sections.id")
    change_description: str = Field(...)
    previous_traits: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    new_traits: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    character: Character = Relationship(back_populates="character_changes")
    section: "StorySection" = Relationship(back_populates="character_changes")

# Location model
class LocationBase(SQLModel):
    name: str = Field(...)
    description: str = Field(...)
    attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

class Location(LocationBase, table=True):
    __tablename__ = "locations"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(foreign_key="stories.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    story: Story = Relationship(back_populates="locations")
    location_changes: List["LocationChange"] = Relationship(back_populates="location")
    events: List["Event"] = Relationship(back_populates="location")

class LocationChange(SQLModel, table=True):
    __tablename__ = "location_changes"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    location_id: str = Field(foreign_key="locations.id")
    section_id: str = Field(foreign_key="story_sections.id")
    change_description: str = Field(...)
    previous_attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    new_attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    location: Location = Relationship(back_populates="location_changes")
    section: "StorySection" = Relationship(back_populates="location_changes")

# Entity Relationship model
class EntityRelationship(SQLModel, table=True):
    __tablename__ = "entity_relationships"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    source_character_id: Optional[str] = Field(default=None, foreign_key="characters.id")
    target_character_id: Optional[str] = Field(default=None, foreign_key="characters.id")
    relationship_type: RelationshipType = Field(default=RelationshipType.UNKNOWN)
    strength: float = Field(default=1.0)  # 0-10 scale for relationship strength
    attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    source_character: Optional[Character] = Relationship(
        back_populates="relationships_as_source",
        sa_relationship_kwargs={"foreign_keys": "[EntityRelationship.source_character_id]"}
    )
    target_character: Optional[Character] = Relationship(
        back_populates="relationships_as_target",
        sa_relationship_kwargs={"foreign_keys": "[EntityRelationship.target_character_id]"}
    )
    relationship_changes: List["RelationshipChange"] = Relationship(back_populates="relationship")

class RelationshipChange(SQLModel, table=True):
    __tablename__ = "relationship_changes"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    relationship_id: str = Field(foreign_key="entity_relationships.id")
    section_id: str = Field(foreign_key="story_sections.id")
    change_description: str = Field(...)
    previous_type: Optional[RelationshipType] = Field(default=None)
    new_type: Optional[RelationshipType] = Field(default=None)
    previous_strength: Optional[float] = Field(default=None)
    new_strength: Optional[float] = Field(default=None)
    previous_attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    new_attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    relationship: EntityRelationship = Relationship(back_populates="relationship_changes")
    section: "StorySection" = Relationship(back_populates="relationship_changes")

# Event/Plot Point model
class EventBase(SQLModel):
    title: str = Field(...)
    description: str = Field(...)
    importance: float = Field(default=1.0)  # 1-10 scale for plot importance
    attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

class Event(EventBase, table=True):
    __tablename__ = "events"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(foreign_key="stories.id")
    location_id: Optional[str] = Field(default=None, foreign_key="locations.id")
    section_id: str = Field(foreign_key="story_sections.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    story: Story = Relationship(back_populates="events")
    location: Optional[Location] = Relationship(back_populates="events")
    section: "StorySection" = Relationship(back_populates="events")
    participants: List["EventParticipant"] = Relationship(back_populates="event")

class EventParticipant(SQLModel, table=True):
    __tablename__ = "event_participants"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    event_id: str = Field(foreign_key="events.id")
    character_id: str = Field(foreign_key="characters.id")
    role: str = Field(...)  # e.g., "protagonist", "antagonist", "witness"
    
    # Relationships
    event: Event = Relationship(back_populates="participants")
    character: Character = Relationship(back_populates="event_participants")

# Enhanced StorySection model with references to changes
class StorySectionBase(SQLModel):
    text: str = Field(...)
    order: int = Field(...)

class StorySection(StorySectionBase, table=True):
    __tablename__ = "story_sections"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(foreign_key="stories.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    story: Story = Relationship(back_populates="sections")
    character_changes: List[CharacterChange] = Relationship(back_populates="section")
    location_changes: List[LocationChange] = Relationship(back_populates="section")
    relationship_changes: List[RelationshipChange] = Relationship(back_populates="section")
    events: List[Event] = Relationship(back_populates="section")

# Response models
class SectionCreate(SQLModel):
    text: str

class CharacterRead(CharacterBase):
    id: str
    story_id: str
    created_at: datetime
    updated_at: datetime

class LocationRead(LocationBase):
    id: str
    story_id: str
    created_at: datetime
    updated_at: datetime

class EventRead(EventBase):
    id: str
    story_id: str
    location_id: Optional[str]
    section_id: str
    created_at: datetime

class StorySectionRead(StorySectionBase):
    id: str
    story_id: str
    created_at: datetime

class StoryWithFullContext(StoryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    sections: List[StorySectionRead] = []
    characters: List[CharacterRead] = []
    locations: List[LocationRead] = []
    events: List[EventRead] = []