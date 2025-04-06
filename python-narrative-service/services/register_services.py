import logging
from services.registry import registry
from services.story import StoryService
from services.story_section import StorySectionService
from services.character import CharacterService
from services.location import LocationService
from services.relationship import RelationshipService
from services.event import EventService
from services.agents import AgentService

logger = logging.getLogger(__name__)

def register_all_services():
    """Register all service instances in the registry"""
    logger.info("Registering all services...")
    
    # Create service instances
    story_service = StoryService()
    story_section_service = StorySectionService()
    character_service = CharacterService()
    location_service = LocationService()
    relationship_service = RelationshipService()
    event_service = EventService()
    agent_service = AgentService()
    
    # Register in the registry
    registry.register('story_service', story_service)
    registry.register('story_section_service', story_section_service)
    registry.register('character_service', character_service)
    registry.register('location_service', location_service)
    registry.register('relationship_service', relationship_service)
    registry.register('event_service', event_service)
    registry.register('agent_service', agent_service)
    
    logger.info("All services registered successfully")
    
    return registry