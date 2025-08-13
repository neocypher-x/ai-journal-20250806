#!/usr/bin/env python3
"""
Basic test script for v2 excavation functionality.
"""

import asyncio
import json
import pytest
from pprint import pprint

from ai_journal.models import (
    JournalEntry, ExcavationInitRequest, ExcavationStepRequest, 
    ReflectionRequestV2
)
from ai_journal.service import ReflectionService
from ai_journal.config import get_settings, Settings


@pytest.mark.asyncio
async def test_excavation_flow():
    """Test the basic excavation flow."""
    
    # Test journal entry
    journal_text = """
    I've been struggling with my job lately. Every morning I wake up dreading going to work.
    I feel like I'm not making any meaningful progress, and my manager seems to constantly
    question my decisions. I used to love this work, but now I feel trapped. I know I should
    probably look for something new, but I'm scared of making the wrong choice and ending up
    worse off. Sometimes I wonder if the problem is just me - maybe I'm not cut out for this
    type of work anymore.
    """
    
    journal_entry = JournalEntry(text=journal_text.strip())
    
    # Initialize service
    settings = get_settings()
    
    print(f"Using model: {settings.model}")
    print(f"Excavation parameters: tau_high={settings.tau_high}, delta_gap={settings.delta_gap}")
    print(f"Budget limit: {settings.k_budget}, Max hypotheses: {settings.max_hypotheses}")
    print()
    
    service = ReflectionService(
        openai_api_key=settings.openai_api_key,
        model=settings.model,
        settings=settings
    )
    
    print("=== Testing v2 Excavation Flow ===\n")
    
    try:
        # Step 1: Initialize excavation
        print("1. Initializing excavation...")
        init_request = ExcavationInitRequest(
            mode="init",
            journal_entry=journal_entry
        )
        
        response = await service.process_excavation_step(init_request)
        print(f"   Complete: {response.complete}")
        print(f"   State revision: {response.state.revision}")
        print(f"   Hypotheses count: {len(response.state.hypotheses)}")
        print(f"   Next probe: {response.next_probe.question if response.next_probe else 'None'}")
        
        if response.state.hypotheses:
            print("   Generated hypotheses:")
            for i, hyp in enumerate(response.state.hypotheses):
                print(f"     {i+1}. {hyp.text} (confidence: {hyp.confidence:.2f})")
        
        print()
        
        # Step 2: Simulate a few excavation steps
        current_state = response.state
        step_count = 0
        
        # Mock user replies for testing
        mock_replies = [
            "Yes, that sounds right. I do feel like I've lost control over my work situation.",
            "I think it's more about feeling undervalued than just fear of change.",
            "Actually, when I think about it, the main issue is that I don't feel heard or respected."
        ]
        
        while not response.complete and step_count < len(mock_replies):
            step_count += 1
            user_reply = mock_replies[step_count - 1]
            
            print(f"{step_count + 1}. Continuing excavation with reply: '{user_reply[:50]}...'")
            
            continue_request = ExcavationStepRequest(
                mode="continue",
                state=current_state,
                user_reply=user_reply,
                expected_probe_id=current_state.last_probe.probe_id
            )
            
            response = await service.process_excavation_step(continue_request)
            current_state = response.state
            
            print(f"   Complete: {response.complete}")
            print(f"   State revision: {response.state.revision}")
            print(f"   Budget used: {response.state.budget_used}")
            
            if response.complete:
                print(f"   Exit reason: {response.exit_reason}")
                if response.result:
                    print(f"   Confirmed crux: {response.result.confirmed_crux.text}")
                    print(f"   Crux confidence: {response.result.confirmed_crux.confidence:.2f}")
                    print(f"   Secondary themes: {len(response.result.secondary_themes)}")
                break
            else:
                print(f"   Next probe: {response.next_probe.question if response.next_probe else 'None'}")
            
            print()
        
        # Step 3: Test v2 reflection generation if excavation completed
        if response.complete and response.result:
            print("3. Generating v2 reflection from excavation result...")
            
            reflection_request = ReflectionRequestV2(
                from_excavation=response.result,
                enable_scout=False,
                journal_entry=journal_entry
            )
            
            reflection = await service.generate_reflection_v2(reflection_request)
            
            print(f"   Generated reflection with {len(reflection.perspectives.items)} perspectives")
            print(f"   Perspectives from: {[p.framework.value for p in reflection.perspectives.items]}")
            print(f"   Prophecy synthesis length: {len(reflection.prophecy.synthesis)} chars")
            print()
            
        print("=== Test completed successfully! ===")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()


