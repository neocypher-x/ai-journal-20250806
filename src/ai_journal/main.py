"""
FastAPI application for the AI Journal system.
"""

import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from ai_journal.config import get_settings
from ai_journal.models import ReflectionRequest, ReflectionResponse
from ai_journal.service import ReflectionService

# Configure logging for debug output
def configure_logging(debug: bool = False, log_level: str = "INFO"):
    """Configure application logging."""
    # Use debug flag or log_level setting
    if debug:
        level = logging.DEBUG
    else:
        level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
        ],
        force=True  # Override existing configuration
    )
    
    # Set specific loggers for our app
    app_loggers = [
        "ai_journal",
        "ai_journal.oracle", 
        "ai_journal.agents",
        "ai_journal.service",
        "ai_journal.main",
        "root"  # Also set root logger
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Reduce noise from other libraries unless we're in debug mode
    if level != logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    logging.info(f"Logging configured at {logging.getLevelName(level)} level")


# Global service instance
reflection_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global reflection_service
    
    # Startup
    settings = get_settings()
    
    # Configure logging based on settings
    configure_logging(debug=settings.debug, log_level=settings.log_level)
    
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

# Static files setup - mount BEFORE defining routes
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    # Mount static assets with explicit priority
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# API Routes
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/reflections", response_model=ReflectionResponse)
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


# Frontend routes - serve React app
@app.get("/")
async def serve_frontend():
    """Serve the React frontend."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "AI Journal Reflection System", "version": "0.1.0", "note": "Frontend not built yet"}


# Explicit asset routes to ensure they don't get caught by catch-all
@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    """Serve static assets with explicit MIME types."""
    asset_path = static_dir / "assets" / file_path
    if asset_path.exists() and asset_path.is_file():
        # Determine MIME type based on file extension
        mime_type = "text/plain"
        if file_path.endswith(".js"):
            mime_type = "text/javascript"
        elif file_path.endswith(".css"):
            mime_type = "text/css"
        elif file_path.endswith(".json"):
            mime_type = "application/json"
        
        return FileResponse(
            str(asset_path),
            media_type=mime_type,
            headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
        )
    raise HTTPException(status_code=404, detail="Asset not found")


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch all routes and serve React app (for client-side routing)."""
    # Don't intercept API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # For all other routes, serve the React app
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    
    # Fallback if no static files
    raise HTTPException(status_code=404, detail="Page not found")


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "ai_journal.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )