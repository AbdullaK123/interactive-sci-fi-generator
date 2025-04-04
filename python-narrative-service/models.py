from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum

# Helper function to generate UUIDs as strings
def generate_uuid():
    return str(uuid.uuid4())

# Enums
class StoryGenre(str, PyEnum):
    SCIFI = "scifi"
    CYBERPUNK = "cyberpunk"
    SPACE_OPERA = "space_opera"
    DYSTOPIAN = "dystopian"

# Link table for many-to-many relationships if needed later
# class StoryTagLink(SQLModel, table=True):
#     __tablename__ = "story_tag_links"
#     
#     story_id: Optional[str] = Field(default=None, foreign_key="stories.id", primary_key=True)
#     tag_id: Optional[str] = Field(default=None, foreign_key="tags.id", primary_key=True)

# Story model
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

class StoryCreate(StoryBase):
    pass

class StoryRead(StoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Story Section model
class StorySectionBase(SQLModel):
    text: str = Field(...)
    order: int = Field(...)

class SectionCreate(SQLModel):
    text: str

class StorySection(StorySectionBase, table=True):
    __tablename__ = "story_sections"
    
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(foreign_key="stories.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    story: Story = Relationship(back_populates="sections")

class StorySectionCreate(StorySectionBase):
    story_id: str

class StorySectionRead(StorySectionBase):
    id: str
    story_id: str
    created_at: datetime

# Complete Story response model
class StoryWithSections(StoryRead):
    sections: List[StorySectionRead] = []