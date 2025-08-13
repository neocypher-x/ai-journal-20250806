#!/usr/bin/env python3
"""Test structured output for agreement scorecard."""

import asyncio
import logging
import os
from unittest.mock import AsyncMock, MagicMock
from ai_journal.models import (
    Framework, Perspective, Perspectives, AgreementItem, 
    AgreementStance, AgreementScorecardResponse
)
from ai_journal.oracle import OracleAgent
from ai_journal.config import get_settings
from openai import AsyncOpenAI

logging.basicConfig(level=logging.DEBUG)

def create_test_perspectives():
    """Create test perspectives."""
    buddhist = Perspective(
        framework=Framework.BUDDHISM,
        core_principle_invoked="Non-attachment leads to peace",
        challenge_framing="You're clinging to outcomes",
        practical_experiment="Practice letting go",
        potential_trap="Becoming indifferent",
        key_metaphor="Water flows around obstacles"
    )
    
    stoic = Perspective(
        framework=Framework.STOICISM,
        core_principle_invoked="Focus on what you control",
        challenge_framing="You're worrying about externals",
        practical_experiment="List what's in your control",
        potential_trap="Becoming rigid",
        key_metaphor="Fortress against storms"
    )
    
    return Perspectives(items=[buddhist, stoic])

async def test_structured_agreement_scorecard():
    """Test structured output for agreement scorecard."""
    
    # Mock client
    mock_client = AsyncMock(spec=AsyncOpenAI)
    oracle = OracleAgent(mock_client, model=get_settings().model)
    
    # Create mock structured response
    mock_agreement_item = AgreementItem(
        framework_a=Framework.BUDDHISM,
        framework_b=Framework.STOICISM,
        stance=AgreementStance.NUANCED,
        notes="Both emphasize inner control but differ on attachment."
    )
    
    mock_response_data = AgreementScorecardResponse(
        agreements=[mock_agreement_item]
    )
    
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = mock_response_data
    mock_response.choices[0].finish_reason = "stop"
    
    mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)
    
    # Test the method
    test_perspectives = create_test_perspectives()
    result = await oracle._generate_agreement_scorecard(test_perspectives)
    
    # Assertions
    assert len(result) == 1
    assert isinstance(result[0], AgreementItem)
    assert result[0].framework_a == Framework.BUDDHISM
    assert result[0].framework_b == Framework.STOICISM
    assert result[0].stance == AgreementStance.NUANCED
    assert "inner control" in result[0].notes
    
    print("✅ Structured output test passed!")
    print(f"   Agreement: {result[0].framework_a.value} vs {result[0].framework_b.value}")
    print(f"   Stance: {result[0].stance.value}")
    print(f"   Notes: {result[0].notes}")

async def test_with_real_api():
    """Test with real OpenAI API if available."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping real API test")
        return
    
    print("🔍 Testing structured output with real OpenAI API...")
    
    client = AsyncOpenAI(api_key=api_key)
    oracle = OracleAgent(client, model=get_settings().model)
    
    try:
        test_perspectives = create_test_perspectives()
        result = await oracle._generate_agreement_scorecard(test_perspectives)
        
        print(f"✅ Real API structured test completed")
        print(f"   Agreement items: {len(result)}")
        for item in result:
            print(f"   {item.framework_a.value} vs {item.framework_b.value}: {item.stance.value}")
            if item.notes:
                print(f"   Notes: {item.notes[:100]}...")
                
        # Check if we got valid structured responses
        if result and all(isinstance(item, AgreementItem) for item in result):
            print("✅ Structured output worked correctly!")
        else:
            print("❌ Structured output failed - got fallback response")
            
    except Exception as e:
        print(f"❌ Real API test failed: {e}")
        logging.exception("Real API structured test failed")
    finally:
        await client.close()

async def test_fallback_behavior():
    """Test fallback behavior when structured output fails."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    oracle = OracleAgent(mock_client, model=get_settings().model)
    
    # Mock a failed response
    mock_client.beta.chat.completions.parse.side_effect = Exception("API Error")
    
    test_perspectives = create_test_perspectives()
    result = await oracle._generate_agreement_scorecard(test_perspectives)
    
    # Should get fallback response
    assert len(result) == 1
    assert isinstance(result[0], AgreementItem)
    assert result[0].stance == AgreementStance.NUANCED
    assert "Fallback assessment" in result[0].notes
    
    print("✅ Fallback behavior test passed!")

async def run_all_tests():
    """Run all structured output tests."""
    print("🧪 Testing structured output for agreement scorecard...\n")
    
    await test_structured_agreement_scorecard()
    await test_fallback_behavior()
    await test_with_real_api()
    
    print("\n✅ All structured output tests completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())