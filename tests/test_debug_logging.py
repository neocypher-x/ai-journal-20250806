#!/usr/bin/env python3
"""Test script to verify debug logging works."""

import logging
import os
import asyncio
from ai_journal.main import configure_logging
from ai_journal.config import get_settings

async def test_debug_logging():
    """Test that debug logging works properly."""
    
    print("🔍 Testing debug logging configuration...\n")
    
    # Test 1: Default logging (INFO level)
    print("1. Testing default logging (INFO level):")
    configure_logging(debug=False, log_level="INFO")
    
    logging.debug("This DEBUG message should NOT appear")
    logging.info("This INFO message should appear")
    logging.warning("This WARNING message should appear")
    
    print()
    
    # Test 2: Debug logging enabled
    print("2. Testing debug logging (DEBUG level):")
    configure_logging(debug=True)
    
    logging.debug("This DEBUG message should appear")
    logging.info("This INFO message should appear") 
    logging.warning("This WARNING message should appear")
    
    print()
    
    # Test 3: Specific ai_journal logger
    print("3. Testing ai_journal specific logger:")
    ai_journal_logger = logging.getLogger("ai_journal.oracle")
    ai_journal_logger.debug("Oracle DEBUG message - should appear")
    ai_journal_logger.info("Oracle INFO message - should appear")
    
    print()
    
    # Test 4: Settings-based configuration
    print("4. Testing settings-based configuration:")
    settings = get_settings()
    print(f"   Current settings: debug={settings.debug}, log_level={settings.log_level}")
    
    configure_logging(debug=settings.debug, log_level=settings.log_level)
    logging.info(f"Logging configured with settings: debug={settings.debug}, level={settings.log_level}")
    
    print()
    print("✅ Debug logging test completed!")
    print()
    print("🔧 To enable debug logging in your app:")
    print("   Option 1: Set environment variable: export DEBUG=true")
    print("   Option 2: Set environment variable: export LOG_LEVEL=DEBUG") 
    print("   Option 3: Create .env file with: DEBUG=true or LOG_LEVEL=DEBUG")
    print("   Option 4: Run with: poetry run uvicorn ai_journal.main:app --reload --log-level debug")

if __name__ == "__main__":
    asyncio.run(test_debug_logging())