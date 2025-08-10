"""Shared pytest fixtures and configuration."""

import pytest
import os
from unittest.mock import AsyncMock
from ai_journal.models import Framework, Perspective, Perspectives
from ai_journal.oracle import OracleAgent
from openai import AsyncOpenAI

# Doppler environment is loaded automatically when DOPPLER_ENV=1 is set
# The doppler-env package handles this via environment variables
# See .vscode/launch.json for the configuration example


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    return AsyncMock(spec=AsyncOpenAI)


@pytest.fixture
def oracle_agent(mock_openai_client):
    """Create an OracleAgent instance with mocked client."""
    return OracleAgent(mock_openai_client, model="gpt-4o-mini")


@pytest.fixture
def sample_perspectives():
    """Create sample perspectives for testing."""
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
    
    existentialist = Perspective(
        framework=Framework.EXISTENTIALISM,
        core_principle_invoked="Create your own meaning",
        challenge_framing="You're living inauthentically",
        practical_experiment="Make one authentic choice today", 
        potential_trap="Falling into nihilism",
        key_metaphor="Author of your own story"
    )
    
    return Perspectives(items=[buddhist, stoic, existentialist])


@pytest.fixture
def openai_api_key():
    """Get OpenAI API key from environment (for integration tests)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key == "dummy-test-key":
        # Return None for dummy keys to trigger skip
        return None
    return api_key


@pytest.fixture
def skip_if_no_api_key(openai_api_key):
    """Skip test if no OpenAI API key is available."""
    if not openai_api_key:
        pytest.skip("Real OpenAI API key not available (set OPENAI_API_KEY or use Doppler)")
    return openai_api_key