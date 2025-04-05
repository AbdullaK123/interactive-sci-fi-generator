# python-narrative-service/ai/config.py
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Agent system configuration
AGENT_CONFIG = {
    # LLM configuration
    "llm": {
        "provider": os.getenv("AI_PROVIDER", "openai").lower(),
        "model_name": os.getenv("AI_MODEL_NAME", "gpt-3.5-turbo"),
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("AI_MAX_TOKENS", "1000")),
    },
    
    # Character agent settings
    "character_agent": {
        "max_history_items": int(os.getenv("CHARACTER_MAX_HISTORY", "5")),
        "default_importance": float(os.getenv("CHARACTER_DEFAULT_IMPORTANCE", "1.0")),
    },
    
    # World state agent settings
    "world_agent": {
        "physics_strictness": float(os.getenv("WORLD_PHYSICS_STRICTNESS", "0.7")),
        "max_world_changes": int(os.getenv("MAX_WORLD_CHANGES", "5")),
    },
    
    # Memory curator settings
    "memory_agent": {
        "max_memories": int(os.getenv("MAX_MEMORIES", "7")),
        "recency_weight": float(os.getenv("MEMORY_RECENCY_WEIGHT", "0.6")),
        "relevance_threshold": float(os.getenv("MEMORY_RELEVANCE_THRESHOLD", "0.3")),
    },
    
    # Narrative director settings
    "narrative_agent": {
        "min_tension": float(os.getenv("MIN_TENSION", "2.0")),
        "max_tension": float(os.getenv("MAX_TENSION", "8.0")),
        "narrative_options_count": int(os.getenv("NARRATIVE_OPTIONS", "3")),
    },
    
    # Orchestrator settings
    "orchestrator": {
        "cache_timeout": int(os.getenv("ORCHESTRATOR_CACHE_TIMEOUT", "3600")),  # seconds
        "agent_timeout": int(os.getenv("AGENT_TIMEOUT", "30")),  # seconds per agent
        "parallel_execution": os.getenv("PARALLEL_EXECUTION", "false").lower() == "true",
    }
}

def get_agent_config() -> Dict[str, Any]:
    """Get the current agent configuration"""
    return AGENT_CONFIG

def update_agent_config(config_updates: Dict[str, Any]) -> None:
    """Update agent configuration (for runtime changes)"""
    global AGENT_CONFIG
    
    # Deep update of configuration
    for category, category_updates in config_updates.items():
        if category in AGENT_CONFIG:
            if isinstance(category_updates, dict) and isinstance(AGENT_CONFIG[category], dict):
                AGENT_CONFIG[category].update(category_updates)
            else:
                AGENT_CONFIG[category] = category_updates
        else:
            AGENT_CONFIG[category] = category_updates
    
    logger.info(f"Updated agent configuration: {config_updates}")

# Initialize agent system on module load
def initialize_agent_system():
    """Initialize the agent system configuration"""
    logger.info("Initializing agent system with configuration:")
    logger.info(f"LLM Provider: {AGENT_CONFIG['llm']['provider']}")
    logger.info(f"LLM Model: {AGENT_CONFIG['llm']['model_name']}")
    
    # Additional initialization can go here
    
    return True

# Call initialization
agent_system_initialized = initialize_agent_system()