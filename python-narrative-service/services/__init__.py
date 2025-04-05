# services/__init__.py
from services.story import StoryService
from services.story_section import StorySectionService
from services.character import CharacterService
from services.location import LocationService
from services.relationship import RelationshipService
from services.event import EventService

# Instantiate all services
story_service = StoryService()
story_section_service = StorySectionService()
character_service = CharacterService()
location_service = LocationService()
relationship_service = RelationshipService()
event_service = EventService()