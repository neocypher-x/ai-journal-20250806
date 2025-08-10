"""
FastAPI application for the AI Journal system.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_journal.config import get_settings
from ai_journal.models import ReflectionRequest, ReflectionResponse
from ai_journal.service import ReflectionService


# Global service instance
reflection_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global reflection_service
    
    # Startup
    settings = get_settings()
    reflection_service = ReflectionService(
        openai_api_key=settings.openai_api_key,
        model=settings.model
    )
    
    yield
    
    # Shutdown
    if reflection_service:
        await reflection_service.close()


app = FastAPI(
    title="AI Journal Reflection System",
    description="A FastAPI-based agentic system for philosophical journal reflection.",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Journal Reflection System", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/reflections", response_model=ReflectionResponse)
async def create_reflection(request: ReflectionRequest):
    """Generate a philosophical reflection for a journal entry."""
    
    if not reflection_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        reflection = await reflection_service.generate_reflection(request)
        return ReflectionResponse(reflection=reflection)
    
    except Exception as e:
        logging.exception("Failed to generate reflection")
        raise HTTPException(status_code=500, detail=f"Failed to generate reflection: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "ai_journal.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )