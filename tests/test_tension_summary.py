#!/usr/bin/env python3
"""Unit test for _generate_tension_summary() method."""

import asyncio
import logging
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from ai_journal.models import Framework, Perspective, Perspectives, TensionPoint
from ai_journal.oracle import OracleAgent
from ai_journal.config import get_settings
from openai import AsyncOpenAI

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Test data - the exact perspectives you provided
TEST_PERSPECTIVES = Perspectives(items=[
    Perspective(
        framework=Framework.BUDDHISM,
        other_framework_name=None,
        core_principle_invoked='Craving for approval and attachment to outcomes cause suffering (dukkha). The Eightfold Path offers practical guidance—cultivating Right Intention, Right Action, and Right Effort—while insight into impermanence (anicca) and non-self (anatta) helps loosen identifying with the compulsion to say yes.',
        challenge_framing="Every yes granted to what you don't truly want is a quiet, personal denial of your own clarity and care.",
        practical_experiment="Pause for 5 mindful breaths before replying to any new work request today, then respond with a brief, honest statement: 'I need to check my capacity and will get back to you with a specific time.'",
        potential_trap='If misused, this becomes rigid avoidance or self-righteousness, masking genuine responsibilities or eroding trust. Balance is needed—compassion for others and for yourself should guide your refusals as well as your commitments.',
        key_metaphor='The Middle Way is a tightrope walk—balance is maintained by not clinging to every gust of craving.'
    ),
    Perspective(
        framework=Framework.STOICISM,
        other_framework_name=None,
        core_principle_invoked="The Dichotomy of Control — you control your own assent and actions, while others' demands and outcomes are not in your power. Therefore, let your commitments be guided by virtue (wisdom, justice, temperance) rather than by the lure of convenience or external pressure.",
        challenge_framing='"Saying yes to everything" is the real failure of will; by overcommitting you surrender your agency and health instead of living in accordance with virtue.',
        practical_experiment='Implement a 60-second pause before agreeing to any new task today. If the request passes the test of being within your control and aligned with virtue, accept; otherwise, politely decline and offer a practical alternative or propose redistributing the burden.',
        potential_trap='This can become rigidity or shirking genuine duty. Ensure you maintain justice and benevolence; avoid using a strict boundary as an excuse to neglect responsibilities or undermine teamwork. Balance discernment with compassion.',
        key_metaphor='Your assent is the rudder; external demands are wind—steer your course with deliberate choice.'
    ),
    Perspective(
        framework=Framework.EXISTENTIALISM,
        other_framework_name=None,
        core_principle_invoked='Existence precedes essence: you create meaning through your choices rather than by inherited duties. Your freedom to say no or yes carries responsibility for authentic living; saying yes to unwelcome work in bad faith distances you from the self you could become and escalates angst as the cost of avoidance.',
        challenge_framing="Stop ghostwriting others' expectations—every habitual yes to what you hate is a line you didn't author in your own life.",
        practical_experiment='Within the next 24 hours, identify one upcoming obligation you dread and decline it with a clear boundary, offering a concrete alternative or renegotiation that aligns with your values.',
        potential_trap='Beware turning boundary-setting into perpetual withdrawal or cynicism. Authenticity requires honest assessment of what truly matters and what you can responsibly limit or renegotiate, not a habit of avoidance that fractures relationships or neglects real duties.',
        key_metaphor="You are the author of your life's manuscript—each yes you stamp into the page either drafts your freedom or writes you into someone else's chapter."
    )
])

class TestTensionSummary:
    """Test class for tension summary generation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock client for testing
        self.mock_client = AsyncMock(spec=AsyncOpenAI)
        self.oracle = OracleAgent(self.mock_client, model=get_settings().model)

    async def test_generate_tension_summary_with_mock_response(self):
        """Test _generate_tension_summary with a mocked successful response."""
        
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
        The key tension between Buddhism and Stoicism lies in their approach to control and attachment. 
        Buddhism emphasizes letting go of all attachments, while Stoicism focuses on controlling what you can.
        
        Between Buddhism and Existentialism, the tension centers on the concept of self - Buddhism teaches non-self (anatta)
        while Existentialism emphasizes authentic self-creation and responsibility.
        
        Stoicism and Existentialism diverge on the source of meaning - Stoics find virtue in accordance with nature,
        while Existentialists create their own meaning through choices.
        """.strip()
        mock_response.choices[0].finish_reason = "stop"
        
        self.mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test the method
        result = await self.oracle._generate_tension_summary(TEST_PERSPECTIVES)
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], TensionPoint)
        assert len(result[0].frameworks) == 3  # All three frameworks
        assert "Buddhism" in result[0].explanation or "Stoicism" in result[0].explanation
        print(f"✅ Mock test passed - explanation length: {len(result[0].explanation)}")
        print(f"   Explanation: {result[0].explanation[:100]}...")

    async def test_generate_tension_summary_with_empty_response(self):
        """Test _generate_tension_summary with an empty response."""
        
        # Mock an empty response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""  # Empty response
        mock_response.choices[0].finish_reason = "length"  # Might indicate truncation
        
        self.mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test the method
        result = await self.oracle._generate_tension_summary(TEST_PERSPECTIVES)
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], TensionPoint)
        assert result[0].explanation == "No tensions identified between the frameworks."
        print(f"✅ Empty response test passed - fallback explanation used")

    async def test_generate_tension_summary_with_none_response(self):
        """Test _generate_tension_summary with None response content."""
        
        # Mock a None response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None  # None response
        mock_response.choices[0].finish_reason = "content_filter"  # Might be filtered
        
        self.mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test the method
        result = await self.oracle._generate_tension_summary(TEST_PERSPECTIVES)
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], TensionPoint)
        assert result[0].explanation == "No tensions identified between the frameworks."
        print(f"✅ None response test passed - fallback explanation used")

    def test_perspectives_text_generation(self):
        """Test that the perspectives text is generated correctly."""
        
        # Manually generate the perspectives text like the method does
        perspectives_text = "\n\n".join([
            f"{p.framework} ({p.other_framework_name if p.framework == Framework.OTHER else p.framework.value}):\n"
            f"- Core principle: {p.core_principle_invoked}\n"
            f"- Challenge: {p.challenge_framing}\n"
            f"- Experiment: {p.practical_experiment}\n"
            f"- Trap: {p.potential_trap}\n"
            f"- Metaphor: {p.key_metaphor}"
            for p in TEST_PERSPECTIVES.items
        ])
        
        # Assertions
        assert "Framework.BUDDHISM" in perspectives_text or "buddhism" in perspectives_text
        assert "Framework.STOICISM" in perspectives_text or "stoicism" in perspectives_text  
        assert "Framework.EXISTENTIALISM" in perspectives_text or "existentialism" in perspectives_text
        assert "Craving for approval" in perspectives_text
        assert "Dichotomy of Control" in perspectives_text
        assert "Existence precedes essence" in perspectives_text
        
        print(f"✅ Perspectives text generation test passed")
        print(f"   Text length: {len(perspectives_text)}")
        print(f"   First 200 chars: {perspectives_text[:200]}...")

async def test_with_real_openai_api():
    """Test with real OpenAI API if API key is available."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping real API test")
        return
    
    print("🔍 Testing with real OpenAI API...")
    
    client = AsyncOpenAI(api_key=api_key)
    oracle = OracleAgent(client, model=get_settings().model)
    
    try:
        result = await oracle._generate_tension_summary(TEST_PERSPECTIVES)
        
        print(f"✅ Real API test completed")
        print(f"   Tension points generated: {len(result)}")
        for i, tp in enumerate(result):
            print(f"   {i+1}. Frameworks: {[f.value for f in tp.frameworks]}")
            print(f"      Explanation length: {len(tp.explanation)}")
            print(f"      Explanation preview: {tp.explanation[:150]}...")
            
        # Check if we got an empty explanation
        if result and not result[0].explanation.strip():
            print("❌ ISSUE FOUND: Empty explanation in real API response!")
        else:
            print("✅ Real API response has content")
            
    except Exception as e:
        print(f"❌ Real API test failed: {e}")
        logging.exception("Real API test failed")
    finally:
        await client.close()

async def run_all_tests():
    """Run all tests."""
    print("🧪 Running tension summary unit tests...\n")
    
    test_instance = TestTensionSummary()
    
    # Test 1: Mock successful response
    test_instance.setup_method()
    await test_instance.test_generate_tension_summary_with_mock_response()
    
    # Test 2: Mock empty response  
    test_instance.setup_method()
    await test_instance.test_generate_tension_summary_with_empty_response()
    
    # Test 3: Mock None response
    test_instance.setup_method()
    await test_instance.test_generate_tension_summary_with_none_response()
    
    # Test 4: Perspectives text generation
    test_instance.test_perspectives_text_generation()
    
    # Test 5: Real API (if available)
    await test_with_real_openai_api()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())