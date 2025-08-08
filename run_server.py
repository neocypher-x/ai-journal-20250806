#!/usr/bin/env python3
"""
Startup script for the AI Journal Reflection System server.
"""

import os
import sys
import uvicorn

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_journal.config import settings

if __name__ == "__main__":
    print("🚀 Starting AI Journal Reflection System...")
    print(f"📍 Host: {settings.HOST}")
    print(f"🔌 Port: {settings.PORT}")
    print(f"🐛 Debug: {settings.DEBUG}")
    print(f"📊 Log Level: {settings.LOG_LEVEL}")
    print()
    
    uvicorn.run(
        "ai_journal.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )