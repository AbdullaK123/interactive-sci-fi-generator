# utils.py
import logging
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import Callable, Any, TypeVar, Optional, List, Type, Awaitable
from database import get_db
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

T = TypeVar('T')

def ai_operation_handler(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to handle AI operation errors with graceful fallbacks.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"AI error in {func.__name__}: {str(e)}")
            
            # Provide appropriate fallback content based on the function
            if func.__name__ == "generate_story_introduction":
                genre = kwargs.get('genre', 'science fiction')
                theme = kwargs.get('theme', 'exploration')
                setting = kwargs.get('setting', '')
                return f"You find yourself in a {genre} world centered around {theme}. {setting}. What will you do next?"
            
            elif func.__name__ == "generate_story_continuation":
                user_input = kwargs.get('user_input', '')
                return f"The story continues based on your decision: {user_input}. What will you do next?"
            
            elif func.__name__ == "generate_story_suggestions":
                return ["Explore the area", "Talk to someone nearby", "Look for clues"]
            
            else:
                logger.critical(f"Unhandled AI fallback case for {func.__name__}")
                return "The story continues... What will you do next?"
    
    return wrapper

def db_operation_handler(func):
    """
    Decorator to handle database operation errors
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            # If the function is async, await it
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database operation failed")
        except ValueError as e:
            logger.warning(f"Value error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
    return async_wrapper

def api_operation_handler(
    *,
    validation_model: Optional[Type] = None,
    requires_auth: bool = False,
    permissions: Optional[List[str]] = None,
    rate_limit: Optional[int] = None
):
    """
    Decorator to handle common API defensive patterns
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Input validation (if model provided)
            if validation_model:
                # Get the request data from kwargs
                data = None
                for key, value in kwargs.items():
                    if isinstance(value, validation_model):
                        data = value
                        break
                
                # If no data found or validation fails
                if data is None:
                    # Try to find the data in the function parameters
                    for arg in args:
                        if isinstance(arg, validation_model):
                            data = arg
                            break
                    
                    if data is None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Missing or invalid input data"
                        )
            
            # Authentication check (placeholder)
            if requires_auth:
                user = kwargs.get('current_user')
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Permission check
                if permissions and not all(p in user.permissions for p in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, 
                        detail="Insufficient permissions"
                    )
            
            # Call the original function (handle both async and sync functions)
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator