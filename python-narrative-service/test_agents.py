# python-narrative-service/test_agents.py
import asyncio
import logging
from sqlmodel import Session
from database import engine
from ai.agents.orchestrator import AgentOrchestrator
from ai import ai_service
from services import story_service
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_test_story(db: Session):
    """Create a test story for agent testing"""
    logger.info("Creating test story...")
    
    story_data = {
        "genre": "cyberpunk",
        "theme": "rebellion against corporate control",
        "setting": "Neo-Tokyo, 2077, where mega-corporations control every aspect of life"
    }
    
    story = await story_service.create_with_ai_introduction(db, story_data)
    logger.info(f"Created story with ID: {story.id}")
    
    return story

async def test_orchestrator(story_id: str, db: Session):
    """Test the agent orchestrator with a single continuation"""
    logger.info(f"Testing orchestrator for story {story_id}")
    
    # Create the orchestrator
    orchestrator = AgentOrchestrator(ai_service.llm, story_id, db)
    await orchestrator.initialize()
    
    # Generate a continuation
    user_input = "I want to hack into the Nexus Corporation's mainframe to find evidence of their illegal experiments."
    logger.info(f"Generating continuation for input: {user_input}")
    
    continuation = await orchestrator.generate_story_continuation(user_input)
    logger.info(f"Generated continuation: {continuation[:200]}...")
    
    # Generate suggestions
    logger.info("Generating suggestions...")
    suggestions = await orchestrator.generate_story_suggestions()
    logger.info(f"Generated suggestions: {suggestions}")
    
    return continuation, suggestions

async def run_multi_turn_conversation(story_id: str, db: Session, turns: int = 3):
    """Run a multi-turn conversation with the agent system"""
    logger.info(f"Running {turns}-turn conversation for story {story_id}")
    
    # Create the orchestrator
    orchestrator = AgentOrchestrator(ai_service.llm, story_id, db)
    await orchestrator.initialize()
    
    # Sample user inputs for each turn
    user_inputs = [
        "I want to explore the neon-lit streets of Neo-Tokyo.",
        "I'll approach the shady cybernetics dealer in the alley.",
        "I want to negotiate for some illegal combat enhancements."
    ]
    
    results = []
    
    for i in range(min(turns, len(user_inputs))):
        user_input = user_inputs[i]
        logger.info(f"Turn {i+1} - User input: {user_input}")
        
        # Generate continuation
        continuation = await orchestrator.generate_story_continuation(user_input)
        logger.info(f"Turn {i+1} - AI response: {continuation[:200]}...")
        
        # Generate suggestions for next turn
        suggestions = await orchestrator.generate_story_suggestions()
        logger.info(f"Turn {i+1} - Suggestions: {suggestions}")
        
        results.append({
            "turn": i+1,
            "user_input": user_input,
            "continuation": continuation,
            "suggestions": suggestions
        })
    
    return results

async def main():
    """Main test function"""
    logger.info("Starting agent system test")
    
    with Session(engine) as db:
        # Either create a new story or use an existing one
        # Uncomment one of these options:
        
        # Option 1: Create a new test story
        story = await create_test_story(db)
        story_id = story.id
        
        # Option 2: Use an existing story ID
        # story_id = "your-existing-story-id"
        
        logger.info(f"Using story ID: {story_id}")
        
        # Test single continuation
        continuation, suggestions = await test_orchestrator(story_id, db)
        
        # Test multi-turn conversation
        # results = await run_multi_turn_conversation(story_id, db, turns=2)
        
        logger.info("Test completed successfully")

if __name__ == "__main__":
    asyncio.run(main())