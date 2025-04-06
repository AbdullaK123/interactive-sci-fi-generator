# main.py
import uvicorn
import os
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from ai.monitoring import get_operation_metrics, get_story_metrics, reset_metrics
from sqlmodel import Session
from startup import create_app
from services import service_registry
from typing import List
from models import (
    StoryCreate, StoryRead, StoryWithSections,
    StorySection, SectionCreate, CharacterRead, EventRead
)
from database import get_db
from utils import db_operation_handler, api_operation_handler

# Security setup for admin endpoints
API_KEY = os.getenv("ADMIN_API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not API_KEY or api_key_header != API_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate API Key"
        )
    return api_key_header

app = create_app()

@app.get('/health')
def health_check():
    return {"status": "healthy", "service": "narrative-service"}

@app.post('/stories', response_model=StoryWithSections)
@api_operation_handler(validation_model=StoryCreate)
@db_operation_handler
async def create_story(story_data: StoryCreate, db: Session = Depends(get_db)):
    # Create story with AI-generated introduction
    story = await service_registry.get("story_service").create_with_ai_introduction(db, story_data)
    return story

@app.get('/stories', response_model=List[StoryRead])
@api_operation_handler()
@db_operation_handler
async def get_stories(db: Session = Depends(get_db)):
    return await service_registry.get("story_service").get_all(db)

@app.get('/stories/{story_id}', response_model=StoryWithSections)
@api_operation_handler()
@db_operation_handler
async def get_story(story_id: str, db: Session = Depends(get_db)):
    story = await service_registry.get("story_service").get_story_with_sections(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@app.get('/stories/{story_id}/characters', response_model=List[CharacterRead])
@api_operation_handler()
@db_operation_handler
async def get_story_characters(
    story_id: str,
    db: Session = Depends(get_db)
):
    """Get all characters for a specific story"""
    # Check that the story exists
    story = await service_registry.get("story_service").get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    characters = await service_registry.get("character_service").get_characters_by_story_id(db, story_id)
    return characters

@app.get('/stories/{story_id}/events', response_model=List[EventRead])
@api_operation_handler()
@db_operation_handler
async def get_story_events(
    story_id: str,
    db: Session = Depends(get_db)
):
    """Get all events for a specific story"""
    # Check that the story exists
    story = await service_registry.get("story_service").get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    events = await service_registry.get("event_service").get_events_by_story_id(db, story_id)
    return events

@app.post('/stories/{story_id}/sections', response_model=StorySection)
@api_operation_handler(validation_model=SectionCreate)
@db_operation_handler
async def add_story_section(
    story_id: str,
    section_data: SectionCreate,
    db: Session = Depends(get_db)
):
    # First check that the story exists
    story = await service_registry.get("story_service").get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Add the AI-generated continuation using the agent system
    section = await service_registry.get("agent_service").generate_continuation(
        db, 
        story_id, 
        section_data.text
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
    story = await service_registry.get("story_service").get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Generate suggestions using the agent system
    suggestions = await service_registry.get("agent_service").generate_suggestions(
        db, 
        story_id
    )
    return suggestions

@app.post('/stories/{story_id}/analyze', response_model=dict)
@api_operation_handler()
@db_operation_handler
async def analyze_user_input(
    story_id: str,
    input_data: dict,
    db: Session = Depends(get_db)
):
    """Analyze user input without generating a continuation"""
    # Check that the story exists
    story = await service_registry.get("story_service").get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    user_input = input_data.get("text", "")
    if not user_input:
        raise HTTPException(status_code=400, detail="Input text is required")
    
    # Analyze the input
    analysis = await service_registry.get("agent_service").analyze_user_input(
        db,
        story_id,
        user_input
    )
    
    return analysis

@app.get('/admin/metrics', response_model=dict)
@api_operation_handler()
async def get_metrics(api_key: APIKey = Depends(get_api_key)):
    """Get performance metrics for all operations"""
    return {
        "operations": get_operation_metrics(),
        "stories": get_story_metrics()
    }

@app.get('/admin/metrics/operation/{operation_name}', response_model=dict)
@api_operation_handler()
async def get_operation_metrics_endpoint(
    operation_name: str,
    api_key: APIKey = Depends(get_api_key)
):
    """Get performance metrics for a specific operation"""
    metrics = get_operation_metrics(operation_name)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Operation {operation_name} not found")
    return metrics

@app.get('/admin/metrics/story/{story_id}', response_model=dict)
@api_operation_handler()
async def get_story_metrics_endpoint(
    story_id: str,
    api_key: APIKey = Depends(get_api_key)
):
    """Get performance metrics for a specific story"""
    metrics = get_story_metrics(story_id)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found in metrics")
    return metrics

@app.post('/admin/metrics/reset', response_model=dict)
@api_operation_handler()
async def reset_metrics_endpoint(api_key: APIKey = Depends(get_api_key)):
    """Reset all performance metrics"""
    reset_metrics()
    return {"status": "metrics reset successfully"}

@app.post('/admin/orchestrator/reset/{story_id}', response_model=dict)
@api_operation_handler()
@db_operation_handler
async def reset_orchestrator(
    story_id: str,
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Reset the agent orchestrator for a specific story"""
    # Check that the story exists
    story = await service_registry.get("story_service").get_by_id(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Reset the orchestrator
    service_registry.get("agent_service").clear_orchestrator_cache(story_id)
    
    return {"status": f"Orchestrator for story {story_id} reset successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)