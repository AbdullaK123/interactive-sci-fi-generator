import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine
from sqlmodel import SQLModel
import models  # Import all models to ensure they're registered
from services.register_services import register_all_services
from fastapi.middleware.cors import CORSMiddleware
from services.registry import registry
from ai.config import initialize_agent_system

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown logic
    """
    # Startup
    logger.info("Starting application...")
    
    # Register all services
    services = register_all_services()
    
    # Initialize AI agent system
    initialize_agent_system()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Any cleanup code would go here
    
    logger.info("Application shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Interactive Sci-Fi Story Generator",
        description="Generate interactive sci-fi stories with AI agents",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Additional app configuration can be done here
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Next.js dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app