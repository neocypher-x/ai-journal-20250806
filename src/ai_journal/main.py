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
    
    Processes journal entries through multiple philosophy coach agents (Buddhist, Stoic, 
    Existentialist) to provide actionable reflection prompts and concrete guidance.
    
    ## Example Usage:
    
    ```bash
    # Basic journal reflection
    curl -X POST "http://localhost:8000/reflect" \
         -H "Content-Type: application/json" \
         -d '{
           "journal_text": "Today I felt overwhelmed at work but managed to complete my project. I keep wondering if I am focusing on the right priorities in life."
         }'
    
    # With specific question
    curl -X POST "http://localhost:8000/reflect" \
         -H "Content-Type: application/json" \
         -d '{
           "journal_text": "I had a difficult conversation with my partner today about our future plans. We both want different things and I feel torn between following my career ambitions and prioritizing our relationship.",
           "question": "How can I navigate this conflict between personal ambition and relationship needs?"
         }'
    
    # Example with longer journal entry
    curl -X POST "http://localhost:8000/reflect" \
         -H "Content-Type: application/json" \
         -d '{
           "journal_text": "This morning I woke up feeling anxious about the presentation I have to give next week. Despite having prepared extensively, I keep doubting myself and imagining all the ways it could go wrong. I noticed that this pattern of catastrophic thinking has been happening more frequently lately, especially around work situations where I feel like I am being evaluated. I took a few deep breaths and tried to remind myself of past successes, but the worry persists. I wonder if this anxiety is trying to tell me something important about my relationship with work and achievement.",
           "question": "What might this anxiety be teaching me about myself?"
         }'
    ```
    
    ## Response Format:
    
    Returns a ReflectResponse with:
    - `summary`: Concise summary of the journal content (≤120 words)
    - `themes`: Key themes identified (1-5 items)  
    - `mood`: Detected emotional state (calm|tense|stressed|sad|angry|energized|mixed)
    - `prompts`: Actionable reflection prompts from different philosophical traditions (max 5)
    - `advice`: Concrete guidance tailored to the journal content (≤120 words)
    - `warnings`: Any processing issues encountered (optional)
    - `trace_id`: Unique identifier for request tracking
    - `processed_at`: Timestamp when request was completed
    
    ## Rate Limiting:
    - 30 requests per minute per IP address
    - 429 status code returned when limit exceeded
    - Retry-After header indicates wait time in seconds
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