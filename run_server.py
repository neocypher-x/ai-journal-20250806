#!/usr/bin/env python3
"""
Development server runner for the AI Journal system.
"""

import uvicorn
from src.ai_journal.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.ai_journal.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )