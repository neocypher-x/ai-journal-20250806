#!/usr/bin/env python3
"""
Simple test script to verify the AI Journal system works.
"""

import asyncio
import json
import os
from ai_journal.models import JournalEntry, ReflectionRequest
from ai_journal.service import ReflectionService


async def test_reflection():
    """Test the reflection generation system."""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it in a .env file or export it as an environment variable")
        return
    
    # Create test journal entry
    journal_text = """
    I keep saying yes to work I don't want to do. Every time my boss asks me to take on another project, 
    I agree even though I'm already overwhelmed. I know I should set boundaries, but I'm afraid of 
    disappointing people or being seen as lazy. Yesterday I agreed to lead a committee I have no interest in, 
    and now I'm resentful and stressed. I feel trapped between wanting to be helpful and needing to 
    protect my own wellbeing.
    """
    
    journal_entry = JournalEntry(text=journal_text.strip())
    request = ReflectionRequest(
        journal_entry=journal_entry,
        enable_scout=True
    )
    
    # Initialize service
    service = ReflectionService(openai_api_key=api_key)
    
    try:
        print("Generating philosophical reflection...")
        print("This may take a few moments as we consult multiple philosophical traditions...\n")
        
        # Generate reflection
        reflection = await service.generate_reflection(request)
        
        # Display results
        print("=" * 80)
        print("PHILOSOPHICAL REFLECTION")
        print("=" * 80)
        print()
        
        print("JOURNAL ENTRY:")
        print(f'"{reflection.journal_entry.text}"')
        print()
        
        print("PHILOSOPHICAL PERSPECTIVES:")
        print("-" * 40)
        
        for i, perspective in enumerate(reflection.perspectives.items, 1):
            framework_name = perspective.other_framework_name if perspective.framework.value == "other" else perspective.framework.value.title()
            print(f"\n{i}. {framework_name} Perspective:")
            print(f"   Core Principle: {perspective.core_principle_invoked}")
            print(f"   Challenge: {perspective.challenge_framing}")
            print(f"   Experiment: {perspective.practical_experiment}")
            print(f"   Potential Trap: {perspective.potential_trap}")
            print(f"   Key Metaphor: {perspective.key_metaphor}")
        
        print("\nORACLE PROPHECY:")
        print("-" * 40)
        
        print(f"\nAgreement Scorecard:")
        for agreement in reflection.prophecy.agreement_scorecard:
            framework_a_name = agreement.framework_a.value.title()
            framework_b_name = agreement.framework_b.value.title()
            print(f"   {framework_a_name} & {framework_b_name}: {agreement.stance.value.upper()}")
            if agreement.notes:
                print(f"      Note: {agreement.notes}")
        
        print(f"\nTension Summary:")
        for tension in reflection.prophecy.tension_summary:
            frameworks = [f.value.title() for f in tension.frameworks]
            print(f"   Frameworks: {', '.join(frameworks)}")
            print(f"   Tension: {tension.explanation}")
        
        print(f"\nSynthesis:")
        print(f"   {reflection.prophecy.synthesis}")
        
        if reflection.prophecy.what_is_lost_by_blending:
            print(f"\nWhat is Lost by Blending:")
            for item in reflection.prophecy.what_is_lost_by_blending:
                print(f"   • {item}")
        
        print("\n" + "=" * 80)
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error during reflection generation: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(test_reflection())