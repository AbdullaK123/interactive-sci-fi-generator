# python-narrative-service/ai/monitoring.py
import time
import logging
import functools
import asyncio
from typing import Dict, Any, List, Callable, Optional, Awaitable
from contextvars import ContextVar

# Setup logging
logger = logging.getLogger(__name__)

# Context variables for tracking operations
current_story_id = ContextVar('current_story_id', default=None)
current_operation = ContextVar('current_operation', default=None)

# Performance metrics storage
agent_metrics = {
    "operation_times": {},  # operation_name -> list of execution times
    "error_counts": {},     # operation_name -> count of errors
    "token_usage": {},      # operation_name -> {prompt_tokens, completion_tokens, total_tokens}
    "total_operations": 0,
    "total_errors": 0,
    "stories": {}           # story_id -> metrics specific to that story
}

def track_agent_operation(operation_name: str):
    """
    Decorator to track performance metrics of agent operations
    
    Args:
        operation_name: Name of the operation being tracked
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get story ID if available
            story_id = kwargs.get('story_id')
            if story_id is None and len(args) > 1:
                # Assume second arg might be story_id in some cases
                potential_story_id = args[1]
                if isinstance(potential_story_id, str):
                    story_id = potential_story_id
            
            # Set context variables
            story_token = None
            if story_id:
                story_token = current_story_id.set(story_id)
            
            operation_token = current_operation.set(operation_name)
            
            # Initialize metrics for this operation if not exists
            if operation_name not in agent_metrics["operation_times"]:
                agent_metrics["operation_times"][operation_name] = []
            
            if operation_name not in agent_metrics["error_counts"]:
                agent_metrics["error_counts"][operation_name] = 0
                
            # Initialize story metrics if needed
            if story_id and story_id not in agent_metrics["stories"]:
                agent_metrics["stories"][story_id] = {
                    "operations": {},
                    "total_operations": 0,
                    "total_errors": 0,
                    "creation_time": time.time()
                }
            
            if story_id and operation_name not in agent_metrics["stories"][story_id]["operations"]:
                agent_metrics["stories"][story_id]["operations"][operation_name] = {
                    "count": 0,
                    "errors": 0,
                    "total_time": 0
                }
            
            start_time = time.time()
            error_occurred = False
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                # Track error
                agent_metrics["error_counts"][operation_name] += 1
                agent_metrics["total_errors"] += 1
                
                if story_id:
                    agent_metrics["stories"][story_id]["operations"][operation_name]["errors"] += 1
                    agent_metrics["stories"][story_id]["total_errors"] += 1
                
                # Re-raise the exception
                raise
            finally:
                # Record execution time
                execution_time = time.time() - start_time
                agent_metrics["operation_times"][operation_name].append(execution_time)
                agent_metrics["total_operations"] += 1
                
                if story_id:
                    story_ops = agent_metrics["stories"][story_id]["operations"][operation_name]
                    story_ops["count"] += 1
                    story_ops["total_time"] += execution_time
                    agent_metrics["stories"][story_id]["total_operations"] += 1
                
                # Log performance
                status = "ERROR" if error_occurred else "SUCCESS"
                logger.info(f"Agent operation: {operation_name} | Duration: {execution_time:.2f}s | Status: {status}")
                
                # Reset context variables
                if story_token:
                    current_story_id.reset(story_token)
                current_operation.reset(operation_token)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # This handles the case where the function is called synchronously
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def log_token_usage(operation_name: str, prompt_tokens: int, completion_tokens: int):
    """
    Log token usage for a specific operation
    
    Args:
        operation_name: Name of the operation
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
    """
    if operation_name not in agent_metrics["token_usage"]:
        agent_metrics["token_usage"][operation_name] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    agent_metrics["token_usage"][operation_name]["prompt_tokens"] += prompt_tokens
    agent_metrics["token_usage"][operation_name]["completion_tokens"] += completion_tokens
    agent_metrics["token_usage"][operation_name]["total_tokens"] += (prompt_tokens + completion_tokens)
    
    # Also track for current story if available
    story_id = current_story_id.get()
    if story_id and story_id in agent_metrics["stories"]:
        if "token_usage" not in agent_metrics["stories"][story_id]:
            agent_metrics["stories"][story_id]["token_usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        
        story_tokens = agent_metrics["stories"][story_id]["token_usage"]
        story_tokens["prompt_tokens"] += prompt_tokens
        story_tokens["completion_tokens"] += completion_tokens
        story_tokens["total_tokens"] += (prompt_tokens + completion_tokens)
    
    logger.debug(f"Token usage for {operation_name}: prompt={prompt_tokens}, completion={completion_tokens}")

def get_operation_metrics(operation_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get metrics for a specific operation or all operations
    
    Args:
        operation_name: Name of the operation to get metrics for, or None for all
        
    Returns:
        Dictionary of metrics
    """
    if operation_name:
        if operation_name not in agent_metrics["operation_times"]:
            return {}
            
        times = agent_metrics["operation_times"][operation_name]
        avg_time = sum(times) / len(times) if times else 0
        
        return {
            "count": len(times),
            "avg_time": avg_time,
            "max_time": max(times) if times else 0,
            "min_time": min(times) if times else 0,
            "errors": agent_metrics["error_counts"].get(operation_name, 0),
            "token_usage": agent_metrics["token_usage"].get(operation_name, {})
        }
    else:
        # Get metrics for all operations
        all_metrics = {}
        for op_name in agent_metrics["operation_times"]:
            all_metrics[op_name] = get_operation_metrics(op_name)
            
        return all_metrics

def get_story_metrics(story_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get metrics for a specific story or all stories
    
    Args:
        story_id: ID of the story to get metrics for, or None for all
        
    Returns:
        Dictionary of metrics
    """
    if story_id:
        return agent_metrics["stories"].get(story_id, {})
    else:
        return {
            "story_count": len(agent_metrics["stories"]),
            "total_operations": agent_metrics["total_operations"],
            "total_errors": agent_metrics["total_errors"],
            "stories": list(agent_metrics["stories"].keys())
        }

def reset_metrics():
    """Reset all metrics"""
    global agent_metrics
    agent_metrics = {
        "operation_times": {},
        "error_counts": {},
        "token_usage": {},
        "total_operations": 0,
        "total_errors": 0,
        "stories": {}
    }
    logger.info("Agent metrics have been reset")