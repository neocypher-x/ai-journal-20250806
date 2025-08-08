"""
AI Journal Reflection System - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import time
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import logging

from .models import ReflectRequest, ReflectResponse
from .orchestrator import ReflectionOrchestrator, health_check_agents
from .config import settings
from .logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler for startup and shutdown."""
    setup_logging()
    logging.info("AI Journal Reflection System starting up...")
    yield
    logging.info("AI Journal Reflection System shutting down...")


app = FastAPI(
    title="AI Journal Reflection System",
    description="Agentic AI system for philosophical journal reflection",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ReflectionOrchestrator()

# Simple in-memory rate limiter
class InMemoryRateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Clean old requests
        client_requests = self.requests[client_ip]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) >= settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
            return False
        
        # Record this request
        client_requests.append(now)
        return True

rate_limiter = InMemoryRateLimiter()

def get_client_ip(request: Request) -> str:
    """Extract client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"

async def rate_limit_dependency(request: Request):
    """Dependency for rate limiting."""
    client_ip = get_client_ip(request)
    
    if not rate_limiter.is_allowed(client_ip):
        logging.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    return client_ip


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled errors."""
    logging.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error"
            }
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/health/agents")
async def health_check_agents_endpoint():
    """Detailed health check including agent status."""
    try:
        result = await health_check_agents()
        return result
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "agents_working": False
        }


@app.post("/reflect", response_model=ReflectResponse)
async def reflect(
    request: ReflectRequest, 
    client_ip: str = Depends(rate_limit_dependency)
) -> ReflectResponse:
    """
    Main reflection endpoint that processes journal entries and returns
    philosophical reflection prompts and advice.
    """
    try:
        response = await orchestrator.process_reflection(request)
        return response
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout - please try again")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.exception("Error processing reflection request")
        raise HTTPException(status_code=500, detail="Failed to process reflection")


if __name__ == "__main__":
    uvicorn.run(
        "ai_journal.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )