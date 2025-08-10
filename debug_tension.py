#!/usr/bin/env python3
"""Debug script for tension summary issue."""

import logging
import asyncio
import os
from ai_journal.models import JournalEntry, Perspective, Perspectives, Framework
from ai_journal.oracle import OracleAgent
from openai import AsyncOpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)

async def debug_tension_summary():
    """Debug the tension summary generation."""
    
    # Check if we have an API key (you'll need to set this)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return
    
    # Create a simple test case
    client = AsyncOpenAI(api_key=api_key)
    oracle = OracleAgent(client, model="gpt-4o-mini")
    
    # Create mock perspectives
    buddhist_perspective = Perspective(
        framework=Framework.BUDDHISM,
        core_principle_invoked="Attachment causes suffering; non-attachment brings peace.",
        challenge_framing="You're clinging to outcomes.",
        practical_experiment="Practice letting go of one expectation today.",
        potential_trap="Confusing detachment with indifference.",
        key_metaphor="Like water flowing around stones."
    )
    
    stoic_perspective = Perspective(
        framework=Framework.STOICISM,
        core_principle_invoked="Focus only on what you can control.",
        challenge_framing="You're worrying about externals.",
        practical_experiment="List what's in your control vs. not.",
        potential_trap="Becoming emotionally suppressed.",
        key_metaphor="Like a fortress weathering storms."
    )
    
    perspectives = Perspectives(items=[buddhist_perspective, stoic_perspective])
    
    print("🔍 Testing tension summary generation...")
    print(f"Perspectives count: {len(perspectives.items)}")
    
    try:
        tension_points = await oracle._generate_tension_summary(perspectives)
        print(f"✅ Generated {len(tension_points)} tension points")
        for i, tp in enumerate(tension_points):
            print(f"  {i+1}. Frameworks: {tp.frameworks}")
            print(f"     Explanation: {tp.explanation[:100]}...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("Failed to generate tension summary")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(debug_tension_summary())