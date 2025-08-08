"""
Logging configuration for the AI Journal Reflection System.
"""

import logging
import sys
import hashlib
from typing import Any, Dict
from .config import settings


class RedactingFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive information."""
    
    def format(self, record):
        # Create a copy of the record to avoid modifying the original
        new_record = logging.makeLogRecord(record.__dict__)
        
        # Redact journal text if present in the message
        if hasattr(new_record, 'journal_text') and settings.REDACT_INPUTS:
            # Replace with hash for tracing purposes
            text_hash = hashlib.sha256(new_record.journal_text.encode()).hexdigest()[:12]
            new_record.journal_text = f"[REDACTED:hash={text_hash}]"
        
        # Check for journal text in the message itself
        if settings.REDACT_INPUTS and hasattr(new_record, 'msg'):
            msg = str(new_record.msg)
            # Simple heuristic: if message is very long, it might contain journal text
            if len(msg) > 200 and any(word in msg.lower() for word in ['dear diary', 'today', 'feel', 'think']):
                text_hash = hashlib.sha256(msg.encode()).hexdigest()[:12]
                new_record.msg = f"[LONG_TEXT_REDACTED:hash={text_hash}]"
        
        return super().format(new_record)


def setup_logging():
    """Configure application logging."""
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Create formatter
    formatter = RedactingFormatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # Create application logger
    app_logger = logging.getLogger("ai_journal")
    app_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    return app_logger


def log_agent_call(agent_name: str, trace_id: str, success: bool, 
                  duration_ms: int, tokens_used: int = None, error: str = None):
    """Log agent call with standardized format."""
    logger = logging.getLogger("ai_journal.agents")
    
    log_data = {
        "agent": agent_name,
        "trace_id": trace_id,
        "success": success,
        "duration_ms": duration_ms,
        "tokens_used": tokens_used
    }
    
    if success:
        logger.info(f"Agent call completed: {log_data}")
    else:
        log_data["error"] = error
        logger.error(f"Agent call failed: {log_data}")


def log_request_metrics(trace_id: str, total_duration_ms: int, 
                       agent_count: int, prompts_generated: int, 
                       dedupe_rate: float = None):
    """Log request-level metrics."""
    logger = logging.getLogger("ai_journal.metrics")
    
    metrics = {
        "trace_id": trace_id,
        "total_duration_ms": total_duration_ms,
        "agents_called": agent_count,
        "prompts_generated": prompts_generated,
        "dedupe_rate": dedupe_rate
    }
    
    logger.info(f"Request metrics: {metrics}")


def create_trace_logger(trace_id: str):
    """Create a logger with trace ID context."""
    logger = logging.getLogger("ai_journal")
    
    class TraceAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return f"[{trace_id[:8]}] {msg}", kwargs
    
    return TraceAdapter(logger, {})