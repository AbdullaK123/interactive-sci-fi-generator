# python-narrative-service/ai/error_handling.py
import logging
import traceback
import functools
from typing import Any, Callable, Dict, Type, Optional, List, TypeVar, Awaitable
import inspect

logger = logging.getLogger(__name__)

# Type variable for return value
T = TypeVar('T')

def agent_error_handler(
    fallback_return: Optional[Any] = None,
    fallback_factory: Optional[Callable[[Exception, Dict[str, Any]], Any]] = None,
    log_level: int = logging.ERROR
):
    """
    Decorator for centralized error handling in the agent system.
    
    Can be configured to provide fallback values and custom error logging.
    
    Args:
        fallback_return: Fixed value to return in case of error
        fallback_factory: Function that produces a fallback value based on the error and args
        log_level: Logging level to use for errors
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            agent_name = args[0].__class__.__name__ if args else "UnknownAgent"
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log the error with appropriate level
                error_message = f"Error in {agent_name}.{func_name}: {str(e)}"
                logger.log(log_level, error_message)
                logger.debug(traceback.format_exc())
                
                # Generate fallback based on configuration
                if fallback_factory is not None:
                    # Build args_dict for context
                    args_dict = {}
                    if args:
                        # Get parameter names for the function
                        sig = inspect.signature(func)
                        param_names = list(sig.parameters.keys())
                        
                        # Map positional args to named parameters, excluding 'self'
                        start_idx = 1 if param_names and param_names[0] == 'self' else 0
                        for i, arg_val in enumerate(args[start_idx:], start_idx):
                            if i < len(param_names):
                                args_dict[param_names[i]] = arg_val
                    
                    # Add keyword args
                    args_dict.update(kwargs)
                    
                    # Call factory with error and arguments
                    return fallback_factory(e, args_dict)
                else:
                    return fallback_return
                    
        return wrapper
    return decorator

# Specialized handlers for different agent functions

def character_agent_fallback(error: Exception, args: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback for character agent operations"""
    return {
        "reasoning": f"Error occurred: {str(error)}",
        "action": "Default action due to processing error",
        "dialogue": "...",
        "emotions": {"neutral": 1.0},
        "motivation": "Continue participation in the story"
    }

def memory_curator_fallback(error: Exception, args: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback for memory curator operations"""
    return {
        "reasoning": f"Error occurred: {str(error)}",
        "action": "Default memory curation",
        "selected_memories": [],
        "relevance_reasoning": "Unable to retrieve memories due to error"
    }

def narrative_director_fallback(error: Exception, args: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback for narrative director operations"""
    return {
        "reasoning": f"Error occurred: {str(error)}",
        "action": "Continue existing narrative",
        "narrative_options": [
            {"description": "Continue current path", "impact_rating": 5.0, "tension_change": 0.0}
        ],
        "selected_direction": "Continue with the current narrative thread",
        "pacing_assessment": "Maintain current pacing",
        "tension_level": 5.0
    }

def world_state_fallback(error: Exception, args: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback for world state operations"""
    return {
        "reasoning": f"Error occurred: {str(error)}",
        "action": "Maintain world consistency",
        "world_effects": ["No significant effects due to processing error"],
        "consistency_issues": [],
        "physics_allowed": True  # Default to allowing actions
    }

def story_continuation_fallback(error: Exception, args: Dict[str, Any]) -> str:
    """Fallback for story continuation generation"""
    user_input = args.get("user_input", "proceed")
    
    # Create a basic continuation that acknowledges the user input
    return f"""You decide to {user_input.lower() if not user_input.lower().startswith('i ') else user_input[2:].lower()}.

The world around you responds to your actions. Despite some uncertainty about what happens next, you continue forward with determination.

What will you do next?"""

def story_suggestions_fallback(error: Exception, args: Dict[str, Any]) -> List[str]:
    """Fallback for story suggestions"""
    return [
        "Explore your surroundings",
        "Talk to someone nearby",
        "Look for clues or useful items"
    ]