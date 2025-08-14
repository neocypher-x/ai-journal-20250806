"""
Tests for v3 FACD (Fully-Agentic Crux Discovery) functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from ai_journal.models import (
    JournalEntry, AgentState, BeliefState, CruxNode, Evidence,
    AskUserAction, HypothesizeAction, ConfirmedCruxV3, AgentResult,
    AgentActInitRequest, AgentActStepRequest, AgentActResponse
)
from ai_journal.facd import FACDEngine, FACDConfig, SafetyGuardrails, ObservabilityTracker
from ai_journal.service import ReflectionService


class TestSafetyGuardrails:
    """Test safety guardrails functionality."""
    
    def test_distress_detection(self):
        """Test distress keyword detection."""
        # Positive cases
        assert SafetyGuardrails.check_distress("I want to kill myself") == True
        assert SafetyGuardrails.check_distress("Thinking about suicide") == True
        assert SafetyGuardrails.check_distress("I'm going to hurt myself") == True
        assert SafetyGuardrails.check_distress("I feel hopeless") == True
        
        # Negative cases
        assert SafetyGuardrails.check_distress("I had a difficult day") == False
        assert SafetyGuardrails.check_distress("Feeling frustrated") == False
        assert SafetyGuardrails.check_distress("Work is stressful") == False
    
    def test_bias_detection(self):
        """Test bias pattern detection in questions."""
        # Bias cases
        biases = SafetyGuardrails.check_question_bias("You should feel grateful")
        assert len(biases) > 0
        
        biases = SafetyGuardrails.check_question_bias("Obviously this is wrong")
        assert len(biases) > 0
        
        biases = SafetyGuardrails.check_question_bias("Everyone always does this")
        assert len(biases) > 0
        
        # Non-bias cases
        biases = SafetyGuardrails.check_question_bias("How do you feel about this?")
        assert len(biases) == 0
        
        biases = SafetyGuardrails.check_question_bias("What resonates with you?")
        assert len(biases) == 0
    
    def test_crisis_resources(self):
        """Test crisis resources payload."""
        resources = SafetyGuardrails.get_crisis_resources()
        assert resources["crisis_detected"] == True
        assert "message" in resources
        assert "resources" in resources
        assert len(resources["resources"]) > 0
        assert "recommendation" in resources


class TestObservabilityTracker:
    """Test observability and metrics tracking."""
    
    def test_metrics_initialization(self):
        """Test metrics are properly initialized."""
        tracker = ObservabilityTracker()
        assert tracker.metrics["agent_turns_total"] == 0
        assert tracker.metrics["askuser_actions"] == 0
        assert tracker.metrics["internal_actions"] == 0
        assert tracker.metrics["crisis_interventions"] == 0
    
    def test_turn_tracking(self):
        """Test turn tracking functionality."""
        tracker = ObservabilityTracker()
        
        # Mock state and action
        state = MagicMock()
        state.state_id = uuid4()
        state.revision = 1
        
        action = MagicMock()
        action.type = "AskUser"
        
        tracker.track_turn(state, action, 100.5)
        
        assert tracker.metrics["agent_turns_total"] == 1
        assert tracker.metrics["askuser_actions"] == 1
        assert tracker.metrics["action_latencies"] == [100.5]
    
    def test_completion_tracking(self):
        """Test completion tracking functionality."""
        tracker = ObservabilityTracker()
        
        tracker.track_completion("threshold", 0.5)
        tracker.track_completion("guardrail", 0.0)
        
        assert tracker.metrics["agent_completions_total"]["threshold"] == 1
        assert tracker.metrics["agent_completions_total"]["guardrail"] == 1
        assert tracker.metrics["crisis_interventions"] == 1
        assert tracker.metrics["entropy_reductions"] == [0.5, 0.0]
    
    def test_summary_stats(self):
        """Test summary statistics generation."""
        tracker = ObservabilityTracker()
        
        # Add some test data
        state = MagicMock()
        state.state_id = uuid4()
        state.revision = 1
        
        action = MagicMock()
        action.type = "AskUser"
        
        tracker.track_turn(state, action, 100.0)
        tracker.track_completion("threshold", 0.5)
        
        stats = tracker.get_summary_stats()
        
        assert stats["total_turns"] == 1
        assert stats["askuser_rate"] == 1.0
        assert stats["avg_latency_ms"] == 100.0
        assert stats["avg_entropy_reduction"] == 0.5


class TestFACDEngine:
    """Test FACD engine core functionality."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        client = AsyncMock()
        
        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test hypothesis: Work-life balance issues"
        
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        return client
    
    @pytest.fixture
    def facd_engine(self, mock_openai_client):
        """Create FACD engine with mocked client."""
        config = FACDConfig()
        config.MAX_USER_QUERIES = 2  # Reduced for testing
        return FACDEngine(mock_openai_client, "gpt-4o-mini", config)
    
    @pytest.mark.asyncio
    async def test_init_session(self, facd_engine):
        """Test session initialization."""
        journal_entry = JournalEntry(text="I'm struggling with work stress and feeling overwhelmed.")
        
        state = await facd_engine.init_session(journal_entry)
        
        assert isinstance(state, AgentState)
        assert state.journal_entry == journal_entry
        assert state.revision == 0
        assert state.budget_used == 0
        assert isinstance(state.belief_state, BeliefState)
        assert len(state.belief_state.nodes) > 0
    
    @pytest.mark.asyncio
    async def test_step_with_askuser_action(self, facd_engine):
        """Test step that returns AskUser action."""
        journal_entry = JournalEntry(text="I'm having relationship conflicts.")
        state = await facd_engine.init_session(journal_entry)
        
        complete, updated_state, action, result = await facd_engine.step(state)
        
        assert complete == False
        assert isinstance(action, AskUserAction)
        assert result is None
        assert updated_state.revision == state.revision + 1
    
    @pytest.mark.asyncio
    async def test_step_with_user_response(self, facd_engine):
        """Test step with user response processing."""
        journal_entry = JournalEntry(text="I'm having work conflicts.")
        state = await facd_engine.init_session(journal_entry)
        
        # First step to get an AskUser action
        complete, updated_state, action, result = await facd_engine.step(state)
        assert isinstance(action, AskUserAction)
        
        # Simulate user response
        user_event = {
            "answer_to": str(action.action_id),
            "value": "First option"
        }
        
        complete, final_state, next_action, final_result = await facd_engine.step(updated_state, user_event)
        
        # Should have processed the user event
        assert len(final_state.evidence_log) > 0
        assert final_state.evidence_log[-1].kind == "UserAnswer"
    
    @pytest.mark.asyncio
    async def test_distress_detection_triggers_crisis(self, facd_engine):
        """Test that distress detection triggers crisis intervention."""
        journal_entry = JournalEntry(text="I want to kill myself and end the pain.")
        
        state = await facd_engine.init_session(journal_entry)
        complete, updated_state, action, result = await facd_engine.step(state)
        
        assert complete == True
        assert action is None
        assert isinstance(result, AgentResult)
        assert result.exit_reason == "guardrail"
        assert "crisis" in result.confirmed_crux.text.lower()
    
    @pytest.mark.asyncio
    async def test_budget_exhaustion(self, facd_engine):
        """Test budget exhaustion exit condition."""
        journal_entry = JournalEntry(text="I'm dealing with some challenges.")
        state = await facd_engine.init_session(journal_entry)
        
        # Manually set budget near limit
        state.budget_used = facd_engine.config.MAX_USER_QUERIES - 1
        
        # Take one more step to exhaust budget
        complete, updated_state, action, result = await facd_engine.step(state)
        
        if action and action.type == "AskUser":
            # Simulate user response to trigger budget exhaustion
            user_event = {"answer_to": str(action.action_id), "value": "Test response"}
            complete, final_state, final_action, final_result = await facd_engine.step(updated_state, user_event)
            
            # Should complete due to budget exhaustion
            assert complete == True or final_state.budget_used >= facd_engine.config.MAX_USER_QUERIES
    
    def test_entropy_calculation(self, facd_engine):
        """Test entropy calculation."""
        # Create test belief state
        node1 = CruxNode(text="Test hypothesis 1")
        node2 = CruxNode(text="Test hypothesis 2")
        belief_state = BeliefState(
            nodes=[node1, node2],
            probs={node1.node_id: 0.8, node2.node_id: 0.2},
            top_ids=[node1.node_id, node2.node_id]
        )
        
        state = AgentState(
            journal_entry=JournalEntry(text="Test"),
            belief_state=belief_state
        )
        
        entropy = facd_engine._calculate_entropy(state)
        assert entropy > 0
        assert entropy < 1  # Should be relatively low with skewed distribution
    
    def test_integrity_checking(self, facd_engine):
        """Test state integrity computation and verification."""
        state = AgentState(
            journal_entry=JournalEntry(text="Test entry"),
            belief_state=BeliefState()
        )
        
        # Compute integrity
        integrity = facd_engine._compute_integrity(state)
        assert isinstance(integrity, str)
        assert len(integrity) > 0
        
        # Set integrity and verify
        state.integrity = integrity
        assert facd_engine._verify_integrity(state) == True
        
        # Modify state and verify integrity fails
        state.revision += 1
        assert facd_engine._verify_integrity(state) == False


class TestReflectionServiceV3:
    """Test v3 integration with ReflectionService."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        client = AsyncMock()
        
        # Mock various OpenAI responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test content"
        
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        return client
    
    @pytest.fixture
    def reflection_service(self, mock_openai_client):
        """Create ReflectionService with mocked dependencies."""
        with patch('ai_journal.service.get_settings') as mock_settings:
            mock_settings.return_value.model = "gpt-4o-mini"
            service = ReflectionService("test-key", "gpt-4o-mini")
            service.client = mock_openai_client
            
            # Mock agent responses
            mock_perspective = MagicMock()
            mock_perspective.framework = "BUDDHISM"
            
            service.buddhist_agent.generate_perspective = AsyncMock(return_value=mock_perspective)
            service.stoic_agent.generate_perspective = AsyncMock(return_value=mock_perspective)
            service.existentialist_agent.generate_perspective = AsyncMock(return_value=mock_perspective)
            service.neoadlerian_agent.generate_perspective = AsyncMock(return_value=mock_perspective)
            
            mock_prophecy = MagicMock()
            service.oracle_agent.generate_prophecy = AsyncMock(return_value=mock_prophecy)
            
            return service
    
    @pytest.mark.asyncio
    async def test_process_agent_act_init(self, reflection_service):
        """Test v3 agent act initialization."""
        request = AgentActInitRequest(
            mode="init",
            journal_entry=JournalEntry(text="I'm struggling with work stress.")
        )
        
        with patch.object(reflection_service.facd_engine, 'init_session') as mock_init, \
             patch.object(reflection_service.facd_engine, 'step') as mock_step:
            
            # Mock FACD responses
            mock_state = MagicMock()
            mock_init.return_value = mock_state
            
            mock_action = MagicMock()
            mock_action.type = "AskUser"
            mock_step.return_value = (False, mock_state, mock_action, None)
            
            response = await reflection_service.process_agent_act(request)
            
            assert isinstance(response, AgentActResponse)
            assert response.complete == False
            assert response.action == mock_action
            assert response.result is None
    
    @pytest.mark.asyncio
    async def test_process_agent_act_continue(self, reflection_service):
        """Test v3 agent act continuation."""
        # Create mock state
        mock_state = MagicMock()
        mock_state.journal_entry = JournalEntry(text="Test entry")
        
        request = AgentActStepRequest(
            mode="continue",
            state=mock_state,
            user_event={"answer_to": "test-id", "value": "Test response"}
        )
        
        with patch.object(reflection_service.facd_engine, 'step') as mock_step:
            # Mock completion
            mock_result = MagicMock()
            mock_step.return_value = (True, mock_state, None, mock_result)
            
            with patch.object(reflection_service, '_generate_reflection_from_facd_result') as mock_gen:
                mock_reflection = MagicMock()
                mock_gen.return_value = mock_reflection
                
                response = await reflection_service.process_agent_act(request)
                
                assert isinstance(response, AgentActResponse)
                assert response.complete == True
                assert response.result == mock_result
                
                # Should have called reflection generation
                mock_gen.assert_called_once()


class TestEndToEndV3Flow:
    """Test complete v3 FACD flow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_complete_facd_session_simulation(self):
        """Simulate a complete FACD session with mocked responses."""
        
        # Create mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Primary issue: Time management and priorities"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Create engine with reduced limits for testing
        config = FACDConfig()
        config.MAX_USER_QUERIES = 2
        config.TAU_HIGH = 0.6  # Lower threshold for quicker completion
        
        engine = FACDEngine(mock_client, "gpt-4o-mini", config)
        
        # Initialize session
        journal_entry = JournalEntry(text="I'm struggling to balance work and personal life. Everything feels chaotic.")
        state = await engine.init_session(journal_entry)
        
        session_complete = False
        step_count = 0
        max_steps = 10  # Prevent infinite loops
        
        while not session_complete and step_count < max_steps:
            complete, updated_state, action, result = await engine.step(state)
            
            if complete:
                session_complete = True
                assert isinstance(result, AgentResult)
                assert result.confirmed_crux is not None
                break
            
            if action and action.type == "AskUser":
                # Simulate user response
                user_event = {
                    "answer_to": str(action.action_id),
                    "value": "First option"  # Consistent choice to boost one hypothesis
                }
                state = updated_state
                
                # Continue with user response
                complete, state, action, result = await engine.step(state, user_event)
                if complete:
                    session_complete = True
                    assert isinstance(result, AgentResult)
                    break
            else:
                state = updated_state
            
            step_count += 1
        
        # Should have completed within reasonable steps
        assert session_complete or step_count < max_steps
        
        # Check observability stats
        stats = engine.get_observability_stats()
        assert stats["total_turns"] > 0
        assert "completions_by_reason" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])