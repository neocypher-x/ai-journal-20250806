#!/usr/bin/env python3
"""
Basic test script for the AI Journal Reflection System.
"""

import asyncio
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_journal.models import ReflectRequest
from ai_journal.orchestrator import ReflectionOrchestrator
from ai_journal.config import settings


async def test_basic_reflection():
    """Test basic reflection functionality."""
    print("🧪 Testing AI Journal Reflection System...")
    print(f"📋 Configuration:")
    print(f"   - Ingestor Model: {settings.INGESTOR_MODEL}")
    print(f"   - Coach Model: {settings.COACH_MODEL}")
    print(f"   - Max Prompts: {settings.MAX_PROMPTS}")
    print(f"   - Agent Timeout: {settings.AGENT_TIMEOUT_SEC}s")
    print(f"   - Global Timeout: {settings.GLOBAL_TIMEOUT_SEC}s")
    print()
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Please set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        return False
    
    print("✅ OpenAI API key found")
    print()
    
    # Create test journal entry
    test_journal = """
    Today was a challenging day at work. I felt overwhelmed by the number of tasks 
    on my plate and struggled to prioritize effectively. Despite feeling stressed, 
    I managed to complete the most important project deadline. I'm grateful for my 
    team's support, but I worry I'm not being as present for my family as I should be. 
    
    I've been thinking about what really matters to me - is it the career advancement 
    I've been pushing for, or the quiet moments with loved ones that I often miss? 
    There's a constant tension between ambition and contentment that I can't seem to resolve.
    
    On the positive side, I did take a 10-minute walk during lunch, which helped clear 
    my head. Small victories, I suppose.
    """
    
    test_request = ReflectRequest(
        journal_text=test_journal.strip(),
        question="How can I better balance my ambition with being present for what matters?"
    )
    
    print("📖 Test Journal Entry:")
    print(f"   Length: {len(test_request.journal_text)} characters")
    print(f"   Question: {test_request.question}")
    print()
    
    try:
        print("🔄 Processing reflection request...")
        
        orchestrator = ReflectionOrchestrator()
        response = await orchestrator.process_reflection(test_request)
        
        print("✅ Reflection completed successfully!")
        print()
        
        print("📊 Results:")
        print(f"   📝 Summary: {response.summary}")
        print()
        print(f"   🏷️  Themes: {', '.join(response.themes)}")
        print()
        print(f"   😊 Mood: {response.mood}")
        print()
        print(f"   💭 Prompts ({len(response.prompts)}):")
        for i, prompt in enumerate(response.prompts, 1):
            print(f"      {i}. [{prompt.source.upper()}] {prompt.text}")
            print(f"         Rationale: {prompt.rationale}")
            print()
        
        print(f"   💡 Advice: {response.advice}")
        print()
        
        if response.warnings:
            print(f"   ⚠️  Warnings: {', '.join(response.warnings)}")
            print()
        
        print(f"   🔍 Trace ID: {response.trace_id}")
        print(f"   ⏱️  Processed at: {response.processed_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_check():
    """Test health check functionality."""
    print("\n🩺 Testing health check...")
    
    try:
        from ai_journal.orchestrator import health_check_agents
        result = await health_check_agents()
        
        if result["status"] == "healthy":
            print("✅ Health check passed")
            print(f"   - Agents working: {result['agents_working']}")
            print(f"   - Prompts generated: {result.get('prompts_generated', 'N/A')}")
        else:
            print("❌ Health check failed")
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
        return result["status"] == "healthy"
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


async def main():
    """Main test runner."""
    print("🚀 AI Journal Reflection System - Basic Tests")
    print("=" * 60)
    
    # Test health check first
    health_ok = await test_health_check()
    
    if health_ok:
        # Run main reflection test
        reflection_ok = await test_basic_reflection()
        
        if reflection_ok:
            print("\n🎉 All tests passed! System is working correctly.")
            print("\n🚀 To start the server, run:")
            print("   poetry run python -m ai_journal.main")
            print("   or")
            print("   poetry run uvicorn ai_journal.main:app --reload")
            return 0
        else:
            print("\n❌ Reflection test failed.")
            return 1
    else:
        print("\n❌ Health check failed - cannot proceed with reflection test.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())