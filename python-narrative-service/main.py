# main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session
from typing import List
from models import (
    Story, StoryCreate, StoryRead, StoryWithSections,
    StorySection, StoryGenre, SectionCreate
)
from database import engine, get_db
from services import story_service, story_section_service
from utils import db_operation_handler, api_operation_handler
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Interactive Sci-Fi Story Generator")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/health')
def health_check():
    return {"status": "healthy", "service": "narrative-service"}

@app.post('/stories', response_model=StoryWithSections)
@api_operation_handler(validation_model=StoryCreate)
@db_operation_handler
async def create_story(story_data: StoryCreate, db: Session = Depends(get_db)):
    # Create story with AI-generated introduction
    story = await story_service.create_with_ai_introduction(db, story_data)
    return story

@app.get('/stories', response_model=List[StoryRead])
@api_operation_handler()
@db_operation_handler
async def get_stories(db: Session = Depends(get_db)):
    return await story_service.get_all(db)

@app.get('/stories/{story_id}', response_model=StoryWithSections)
@api_operation_handler()
@db_operation_handler
async def get_story(story_id: str, db: Session = Depends(get_db)):
    story = await story_service.get_story_with_sections(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@app.post('/stories/{story_id}/sections', response_model=StorySection)
@api_operation_handler(validation_model=SectionCreate)
@db_operation_handler
async def add_story_section(
    story_id: str,
    section_data: SectionCreate,
    db: Session = Depends(get_db)
):
    # First check that the story exists
    story = await story_service.get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Add the AI-generated continuation - note the await here
    section = await story_section_service.add_ai_continuation(
        db, 
        story_id, 
        section_data.text,
        story_service
    )
    return section

@app.get('/stories/{story_id}/suggestions', response_model=List[str])
@api_operation_handler()
@db_operation_handler
async def get_story_suggestions(
    story_id: str,
    db: Session = Depends(get_db)
):
    # Check that the story exists
    story = await story_service.get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Generate suggestions
    suggestions = await story_section_service.generate_suggestions(
        db, 
        story_id,
        story_service
    )
    return suggestions

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)