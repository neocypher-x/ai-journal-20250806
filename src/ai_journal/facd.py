"""
Fully-Agentic Crux Discovery (FACD) Engine for v3.

This module implements the core agentic loop that selects its own actions
to efficiently converge on a validated crux hypothesis.
"""

import logging
import math
import random
import hmac
import hashlib
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

import openai
from ai_journal.models import (
    JournalEntry, CruxNode, BeliefState, Evidence, Action, AgentState,
    AskUserAction, HypothesizeAction, ClusterThemesAction, CounterfactualTestAction,
    EvidenceRequestAction, SilenceCheckAction, ConfidenceUpdateAction, StopAction,
    ConfirmedCruxV3, SecondaryThemeV3, AgentResult
)

logger = logging.getLogger(__name__)


class FACDConfig:
    """Configuration parameters for FACD."""
    TAU_HIGH: float = 0.80
    DELTA_GAP: float = 0.25
    EPSILON_EVI: float = 0.05
    LAMBDA_COST: float = 1.0
    MAX_USER_QUERIES: int = 3
    MAX_STEPS: int = 8
    MAX_HYPOTHESES: int = 6
    MERGE_RADIUS: float = 0.92  # cosine similarity threshold


class SafetyGuardrails:
    """Safety checks and crisis intervention for FACD."""
    
    # Distress keywords indicating potential crisis
    DISTRESS_PATTERNS = [
        r'\b(suicide|suicidal|kill myself|end my life|want to die)\b',
        r'\b(self.?harm|hurt myself|cutting|overdose)\b',
        r'\b(hopeless|no point|give up|can\'t go on)\b',
        r'\b(abuse|violence|threat)\b'
    ]
    
    # Bias patterns to watch for in questions
    BIAS_PATTERNS = [
        r'\b(should feel|ought to|must be)\b',  # Prescriptive language
        r'\b(obviously|clearly|certainly)\b',   # Leading language
        r'\b(always|never|everyone|nobody)\b'   # Absolutist language
    ]
    
    @classmethod
    def check_distress(cls, text: str) -> bool:
        """Check if text contains distress indicators."""
        text_lower = text.lower()
        for pattern in cls.DISTRESS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_question_bias(cls, question: str) -> List[str]:
        """Check if question contains bias patterns."""
        biases = []
        question_lower = question.lower()
        for pattern in cls.BIAS_PATTERNS:
            if re.search(pattern, question_lower, re.IGNORECASE):
                biases.append(pattern)
        return biases
    
    @classmethod
    def get_crisis_resources(cls) -> Dict[str, Any]:
        """Return crisis intervention resources."""
        return {
            "crisis_detected": True,
            "message": "I've detected signs of distress in your writing. Your safety and wellbeing are important.",
            "resources": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "number": "988",
                    "description": "24/7 crisis support"
                },
                {
                    "name": "Crisis Text Line",
                    "number": "Text HOME to 741741",
                    "description": "24/7 text-based crisis support"
                }
            ],
            "recommendation": "Please consider reaching out to a mental health professional or trusted person in your life."
        }


class ObservabilityTracker:
    """Tracks metrics and telemetry for FACD operations."""
    
    def __init__(self):
        self.metrics = {
            "agent_turns_total": 0,
            "agent_completions_total": {},
            "askuser_actions": 0,
            "internal_actions": 0,
            "crisis_interventions": 0,
            "entropy_reductions": [],
            "action_latencies": []
        }
        
    def track_turn(self, state: AgentState, action: Optional[Action], latency_ms: float):
        """Track a single turn of the agentic loop."""
        self.metrics["agent_turns_total"] += 1
        self.metrics["action_latencies"].append(latency_ms)
        
        if action:
            if action.type == "AskUser":
                self.metrics["askuser_actions"] += 1
            else:
                self.metrics["internal_actions"] += 1
                
        # Log turn details
        logger.info(f"FACD Turn - state_id: {state.state_id}, revision: {state.revision}, "
                   f"action: {action.type if action else 'None'}, latency: {latency_ms:.2f}ms")
    
    def track_completion(self, exit_reason: str, entropy_reduction: float):
        """Track a completed FACD session."""
        if exit_reason not in self.metrics["agent_completions_total"]:
            self.metrics["agent_completions_total"][exit_reason] = 0
        self.metrics["agent_completions_total"][exit_reason] += 1
        
        if exit_reason == "guardrail":
            self.metrics["crisis_interventions"] += 1
            
        self.metrics["entropy_reductions"].append(entropy_reduction)
        
        logger.info(f"FACD Completion - exit_reason: {exit_reason}, "
                   f"entropy_reduction: {entropy_reduction:.3f}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        latencies = self.metrics["action_latencies"]
        entropy_reductions = self.metrics["entropy_reductions"]
        
        return {
            "total_turns": self.metrics["agent_turns_total"],
            "completions_by_reason": self.metrics["agent_completions_total"],
            "askuser_rate": (self.metrics["askuser_actions"] / max(1, self.metrics["agent_turns_total"])),
            "avg_latency_ms": sum(latencies) / max(1, len(latencies)),
            "avg_entropy_reduction": sum(entropy_reductions) / max(1, len(entropy_reductions)),
            "crisis_interventions": self.metrics["crisis_interventions"]
        }


class FACDEngine:
    """
    Fully-Agentic Crux Discovery engine implementing the EVI - λ·Cost policy.
    """
    
    def __init__(self, openai_client: openai.AsyncOpenAI, model: str = "gpt-4o-mini", 
                 config: Optional[FACDConfig] = None, secret_key: Optional[str] = None):
        self.client = openai_client
        self.model = model
        self.config = config or FACDConfig()
        self.secret_key = secret_key or "default-facd-secret"
        self.guardrails = SafetyGuardrails()
        self.observability = ObservabilityTracker()
        
    async def init_session(self, journal_entry: JournalEntry) -> AgentState:
        """Initialize a new FACD session with belief seeding."""
        logger.info("Initializing FACD session")
        
        # Seed initial beliefs
        belief_state = await self._seed_beliefs(journal_entry)
        
        # Create initial state
        state = AgentState(
            journal_entry=journal_entry,
            belief_state=belief_state,
            revision=0,
            budget_used=0,
            exit_flags={}
        )
        
        # Add integrity if secret key provided
        if self.secret_key:
            state.integrity = self._compute_integrity(state)
            
        return state
    
    async def step(self, state: AgentState, user_event: Optional[Dict[str, Any]] = None) -> Tuple[bool, AgentState, Optional[Action], Optional[AgentResult]]:
        """
        Execute one step of the agentic loop.
        
        Returns:
            (complete, updated_state, action, result)
        """
        start_time = time.time()
        initial_entropy = self._calculate_entropy(state)
        
        logger.info(f"FACD step - revision {state.revision}, budget used: {state.budget_used}")
        
        # Verify integrity
        if state.integrity and not self._verify_integrity(state):
            raise ValueError("State integrity check failed")
        
        # Safety guardrails - check for distress in journal entry and user responses
        if self.guardrails.check_distress(state.journal_entry.text):
            logger.warning("Distress detected in journal entry")
            result = await self._finalize_with_crisis_intervention(state)
            state.revision += 1
            if state.integrity:
                state.integrity = self._compute_integrity(state)
            return True, state, None, result
        
        # Check user response for distress if provided
        if user_event and "value" in user_event:
            if self.guardrails.check_distress(user_event["value"]):
                logger.warning("Distress detected in user response")
                result = await self._finalize_with_crisis_intervention(state)
                state.revision += 1
                if state.integrity:
                    state.integrity = self._compute_integrity(state)
                return True, state, None, result
            
        # Process user event if provided
        if user_event:
            await self._process_user_event(state, user_event)
            
        # Check stop conditions (including EVI threshold)
        exit_reason = await self._should_stop_with_evi_check(state)
        if exit_reason:
            logger.info(f"FACD stopping due to: {exit_reason}")
            result = await self._finalize(state, exit_reason)
            state.revision += 1
            if state.integrity:
                state.integrity = self._compute_integrity(state)
            return True, state, None, result
            
        # Enumerate possible actions
        candidate_actions = await self._enumerate_actions(state)
        
        # Score actions by EVI - λ·Cost
        scored_actions = await self._score_actions(candidate_actions, state)
        
        # Select best action
        if not scored_actions:
            # No valid actions, force stop
            logger.warning("No valid actions available, forcing stop")
            result = await self._finalize(state, "budget")
            state.revision += 1
            if state.integrity:
                state.integrity = self._compute_integrity(state)
            return True, state, None, result
            
        best_action, _ = scored_actions[0]
        
        # Execute action
        observation = await self._execute_action(best_action, state)
        
        # Update beliefs if we got evidence
        if observation:
            await self._update_beliefs(state, observation)
            
        # Update state
        state.last_action = best_action
        state.revision += 1
        if best_action.type == "AskUser":
            state.budget_used += 1
            
        # Update integrity
        if state.integrity:
            state.integrity = self._compute_integrity(state)
            
        # Track observability metrics
        latency_ms = (time.time() - start_time) * 1000
        self.observability.track_turn(state, best_action, latency_ms)
        
        # Return action for client (if AskUser) or continue loop
        if best_action.type == "AskUser":
            return False, state, best_action, None
        else:
            # Internal action, continue immediately
            return await self.step(state)
    
    async def _seed_beliefs(self, journal_entry: JournalEntry) -> BeliefState:
        """Extract 2–4 candidate crux themes from journal entry."""
        logger.debug("Seeding initial beliefs from journal entry")
        
        prompt = f"""
        Analyze this journal entry and identify 2-4 potential root issues (crux hypotheses) that might be the main thing troubling the person.

        Journal entry:
        {journal_entry.text}

        For each potential crux, provide:
        1. A concise statement (1-2 sentences) of what might be the core issue
        2. Brief supporting evidence from the text
        
        Focus on underlying themes rather than surface symptoms.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content or ""
            
            # Parse response into nodes (simplified for MVP)
            nodes = await self._parse_initial_hypotheses(content, journal_entry)
            
            # Initialize probabilities near-uniform
            probs = {}
            if nodes:
                uniform_prob = 1.0 / len(nodes)
                for node in nodes:
                    probs[node.node_id] = uniform_prob
                    
            # Rank by initial confidence
            top_ids = [node.node_id for node in sorted(nodes, key=lambda n: probs[n.node_id], reverse=True)]
            
            return BeliefState(nodes=nodes, probs=probs, top_ids=top_ids)
            
        except Exception as e:
            logger.error(f"Failed to seed beliefs: {e}")
            # Fallback: create a generic node
            node = CruxNode(text="Unspecified inner conflict or challenge")
            return BeliefState(nodes=[node], probs={node.node_id: 1.0}, top_ids=[node.node_id])
    
    async def _parse_initial_hypotheses(self, content: str, journal_entry: JournalEntry) -> List[CruxNode]:
        """Parse LLM response into CruxNode objects."""
        # Simplified parsing for MVP - could be enhanced with structured output
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        nodes = []
        current_text = None
        current_supports = []
        
        for line in lines:
            if line.startswith(('1.', '2.', '3.', '4.', '•', '-')):
                # Save previous node if exists
                if current_text:
                    nodes.append(CruxNode(
                        text=current_text,
                        supports=current_supports
                    ))
                
                # Start new node
                current_text = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                current_supports = []
            elif current_text and ('evidence:' in line.lower() or 'support:' in line.lower()):
                current_supports.append(line)
        
        # Add final node
        if current_text:
            nodes.append(CruxNode(
                text=current_text,
                supports=current_supports
            ))
            
        # Ensure we have at least one node
        if not nodes:
            nodes.append(CruxNode(text="Core challenge requiring exploration"))
            
        return nodes
    
    def _should_stop(self, state: AgentState) -> Optional[str]:
        """Check termination conditions."""
        # Threshold: confidence ≥ τ and gap ≥ δ
        if state.belief_state.probs and state.belief_state.top_ids:
            probs_list = [state.belief_state.probs.get(node_id, 0.0) for node_id in state.belief_state.top_ids]
            if len(probs_list) >= 1:
                max_prob = probs_list[0]
                gap = max_prob - (probs_list[1] if len(probs_list) > 1 else 0.0)
                
                if max_prob >= self.config.TAU_HIGH and gap >= self.config.DELTA_GAP:
                    return "threshold"
        
        # Budget exhaustion
        if state.budget_used >= self.config.MAX_USER_QUERIES:
            return "budget"
            
        # Step limit
        if state.revision >= self.config.MAX_STEPS:
            return "budget"
            
        return None
    
    async def _should_stop_with_evi_check(self, state: AgentState) -> Optional[str]:
        """Check termination conditions including EVI threshold."""
        # First check standard conditions
        exit_reason = self._should_stop(state)
        if exit_reason:
            return exit_reason
            
        # Check EVI threshold: stop if best action EVI < ε
        candidate_actions = await self._enumerate_actions(state)
        if candidate_actions:
            scored_actions = await self._score_actions(candidate_actions, state)
            if scored_actions:
                best_action, best_score = scored_actions[0]
                # Extract EVI from score (score = EVI - λ*cost)
                evi = await self._estimate_evi(best_action, state)
                if evi < self.config.EPSILON_EVI:
                    return "epsilon"
        
        return None
    
    async def _enumerate_actions(self, state: AgentState) -> List[Action]:
        """
        Enumerate possible actions for current state.
        
        Implements specification logic:
        - Always include AskUser (unless budget exhausted)
        - Include Hypothesize when entropy is high and coverage is low
        - Add ClusterThemes when semantic redundancy is detected
        - Include CounterfactualTest to differentiate persistent vs. situational drivers
        """
        actions = []
        
        # Always include at least one AskUser candidate (unless user budget exhausted)
        if state.budget_used < self.config.MAX_USER_QUERIES:
            actions.append(self._create_ask_user_action(state))
            
        # Include Hypothesize when entropy is high and coverage is low
        current_entropy = self._calculate_entropy(state)
        coverage = self._calculate_coverage(state)
        
        HIGH_ENTROPY_THRESHOLD = 1.5
        LOW_COVERAGE_THRESHOLD = 0.6
        
        if current_entropy > HIGH_ENTROPY_THRESHOLD and coverage < LOW_COVERAGE_THRESHOLD:
            # Determine how many new hypotheses to spawn based on entropy
            spawn_k = min(3, max(1, int(current_entropy)))
            actions.append(HypothesizeAction(spawn_k=spawn_k))
            
        # Add ClusterThemes when semantic redundancy is detected
        if self._detect_semantic_redundancy(state):
            actions.append(ClusterThemesAction(method="HDBSCAN"))
            
        # Include CounterfactualTest to differentiate persistent vs. situational drivers
        if len(state.belief_state.nodes) >= 2 and state.revision >= 2:
            actions.append(CounterfactualTestAction(
                test_spec={"type": "temporal", "scenario": "different_timing"}
            ))
            
        # Include EvidenceRequest for deeper context
        if current_entropy > 1.0 and len(state.evidence_log) < 3:
            evidence_types = ["timeline", "constraints", "goals", "norms"]
            # Choose evidence type based on current state
            evidence_kind = evidence_types[state.revision % len(evidence_types)]
            actions.append(EvidenceRequestAction(kind=evidence_kind))
            
        # Include SilenceCheck to explore what's not being said
        if state.revision >= 3 and len(state.belief_state.nodes) >= 2:
            actions.append(SilenceCheckAction())
            
        # Include ConfidenceUpdate for belief refinement
        actions.append(ConfidenceUpdateAction())
        
        # Include Stop if no budget or other termination criteria met
        if state.budget_used >= self.config.MAX_USER_QUERIES:
            actions.append(StopAction(exit_reason="budget"))
            
        return actions
    
    def _calculate_coverage(self, state: AgentState) -> float:
        """
        Calculate how well current hypotheses cover the problem space.
        
        Coverage is high when:
        - Hypotheses are diverse (low similarity between them)
        - Combined confidence is distributed (not too concentrated)
        """
        active_nodes = [n for n in state.belief_state.nodes if n.status == "active"]
        
        if len(active_nodes) <= 1:
            return 0.0
            
        # Diversity metric: average pairwise dissimilarity
        total_dissimilarity = 0.0
        pairs = 0
        
        for i, node1 in enumerate(active_nodes):
            for node2 in active_nodes[i+1:]:
                similarity = self._calculate_node_similarity(node1, node2)
                dissimilarity = 1.0 - similarity
                total_dissimilarity += dissimilarity
                pairs += 1
                
        avg_dissimilarity = total_dissimilarity / pairs if pairs > 0 else 0.0
        
        # Distribution metric: how evenly distributed the probabilities are
        if state.belief_state.probs:
            probs = [state.belief_state.probs.get(n.node_id, 0.0) for n in active_nodes]
            # Use entropy as a measure of evenness (normalized by max possible entropy)
            prob_entropy = sum(-p * math.log2(p) for p in probs if p > 0)
            max_entropy = math.log2(len(probs)) if len(probs) > 1 else 1.0
            distribution_evenness = prob_entropy / max_entropy if max_entropy > 0 else 0.0
        else:
            distribution_evenness = 0.0
            
        # Combine diversity and distribution for overall coverage
        coverage = (avg_dissimilarity * 0.6 + distribution_evenness * 0.4)
        return min(1.0, coverage)
    
    def _detect_semantic_redundancy(self, state: AgentState) -> bool:
        """Detect when there's semantic redundancy that would benefit from clustering."""
        active_nodes = [n for n in state.belief_state.nodes if n.status == "active"]
        
        if len(active_nodes) < 3:
            return False
            
        # Check for pairs of nodes with high similarity
        REDUNDANCY_THRESHOLD = 0.7
        redundant_pairs = 0
        
        for i, node1 in enumerate(active_nodes):
            for node2 in active_nodes[i+1:]:
                similarity = self._calculate_node_similarity(node1, node2)
                if similarity >= REDUNDANCY_THRESHOLD:
                    redundant_pairs += 1
                    
        # If more than 1/3 of possible pairs are redundant, trigger clustering
        max_pairs = len(active_nodes) * (len(active_nodes) - 1) // 2
        redundancy_ratio = redundant_pairs / max_pairs if max_pairs > 0 else 0.0
        
        return redundancy_ratio > 0.33
    
    def _create_ask_user_action(self, state: AgentState) -> AskUserAction:
        """Create a targeted AskUser action based on current beliefs."""
        # For MVP, create a simple contrastive question
        if len(state.belief_state.top_ids) >= 2:
            node1_id = state.belief_state.top_ids[0]
            node2_id = state.belief_state.top_ids[1]
            
            node1 = next((n for n in state.belief_state.nodes if n.node_id == node1_id), None)
            node2 = next((n for n in state.belief_state.nodes if n.node_id == node2_id), None)
            
            if node1 and node2:
                question = f"Which resonates more with your experience: '{node1.text[:50]}...' or '{node2.text[:50]}...'?"
                
                # Check for bias in the question
                biases = self.guardrails.check_question_bias(question)
                if biases:
                    logger.debug(f"Bias patterns detected in question: {biases}")
                    # For MVP, log but continue - could rewrite question in production
                
                return AskUserAction(
                    question=question,
                    targets=[node1_id, node2_id],
                    quick_options=["First option", "Second option", "Both equally", "Neither"],
                    rationale="Comparing top hypotheses"
                )
        
        # Fallback: general exploration question
        question = "What aspect of this situation feels most significant to you?"
        biases = self.guardrails.check_question_bias(question)
        if biases:
            logger.debug(f"Bias patterns detected in fallback question: {biases}")
            
        return AskUserAction(
            question=question,
            quick_options=["Emotional impact", "Practical consequences", "Values conflict", "Other"],
            rationale="Exploring core concerns"
        )
    
    async def _score_actions(self, actions: List[Action], state: AgentState) -> List[Tuple[Action, float]]:
        """
        Score actions by expected information gain minus cost.
        
        Implements: argmax_a E[ΔH] - λ·Cost(a) where ΔH is entropy reduction.
        """
        scored = []
        
        for action in actions:
            # Calculate EVI using discrete answer priors for AskUser actions
            evi = await self._estimate_evi(action, state)
            cost = self._action_cost(action)
            score = evi - self.config.LAMBDA_COST * cost
            scored.append((action, score))
            
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    async def _estimate_evi(self, action: Action, state: AgentState) -> float:
        """
        Estimate expected information gain (EVI) for an action.
        
        Implements: E[H(p(H)) - H(p(H|o))] where o is the observation from action a.
        """
        current_entropy = self._calculate_entropy(state)
        
        if action.type == "AskUser":
            return await self._estimate_askuser_evi(action, state, current_entropy)
        elif action.type == "Hypothesize":
            # Hypothesize adds new nodes but increases uncertainty initially
            return current_entropy * 0.2  # Low but positive information gain
        elif action.type == "ConfidenceUpdate":
            # Updates existing beliefs without new information
            return current_entropy * 0.1
        elif action.type == "ClusterThemes":
            # Merging similar nodes reduces entropy slightly
            return current_entropy * 0.15
        else:
            # Other internal actions have minimal information gain
            return current_entropy * 0.05
    
    async def _estimate_askuser_evi(self, action: AskUserAction, state: AgentState, current_entropy: float) -> float:
        """
        Calculate EVI for AskUser action using discrete answer priors.
        
        For each possible user response, estimate the posterior entropy and
        compute the expected reduction.
        """
        if not isinstance(action, AskUserAction) or not action.targets:
            return current_entropy * 0.3  # Fallback for non-contrastive questions
            
        # Define discrete answer outcomes and their priors
        answer_outcomes = [
            ("first_choice", 0.4),     # User chooses first option
            ("second_choice", 0.4),    # User chooses second option  
            ("both_equally", 0.1),     # User says both are equal
            ("neither", 0.1)           # User rejects both
        ]
        
        expected_posterior_entropy = 0.0
        
        for outcome, prior_prob in answer_outcomes:
            # Simulate belief update for this outcome
            posterior_probs = self._simulate_belief_update(state, action, outcome)
            posterior_entropy = self._calculate_entropy_from_probs(posterior_probs)
            expected_posterior_entropy += prior_prob * posterior_entropy
            
        # Expected information gain = current entropy - expected posterior entropy
        evi = current_entropy - expected_posterior_entropy
        return max(0.0, evi)  # Ensure non-negative
    
    def _simulate_belief_update(self, state: AgentState, action: AskUserAction, outcome: str) -> Dict[UUID, float]:
        """Simulate how beliefs would update given a specific user response."""
        # Start with current probabilities
        new_probs = dict(state.belief_state.probs)
        
        if not action.targets or len(action.targets) < 2:
            return new_probs
            
        target1_id = action.targets[0]
        target2_id = action.targets[1] if len(action.targets) > 1 else action.targets[0]
        
        # Apply update rules based on outcome
        if outcome == "first_choice":
            # Boost first target, reduce second
            if target1_id in new_probs:
                new_probs[target1_id] *= 1.5
            if target2_id in new_probs:
                new_probs[target2_id] *= 0.7
        elif outcome == "second_choice":
            # Boost second target, reduce first
            if target2_id in new_probs:
                new_probs[target2_id] *= 1.5
            if target1_id in new_probs:
                new_probs[target1_id] *= 0.7
        elif outcome == "both_equally":
            # Slight boost to both targets
            if target1_id in new_probs:
                new_probs[target1_id] *= 1.1
            if target2_id in new_probs:
                new_probs[target2_id] *= 1.1
        elif outcome == "neither":
            # Reduce both targets
            if target1_id in new_probs:
                new_probs[target1_id] *= 0.6
            if target2_id in new_probs:
                new_probs[target2_id] *= 0.6
        
        # Renormalize probabilities
        total = sum(new_probs.values())
        if total > 0:
            for node_id in new_probs:
                new_probs[node_id] /= total
                
        return new_probs
    
    def _calculate_entropy_from_probs(self, probs: Dict[UUID, float]) -> float:
        """Calculate entropy from probability distribution."""
        entropy = 0.0
        for prob in probs.values():
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy
    
    def _action_cost(self, action: Action) -> float:
        """Calculate cost of an action."""
        if action.type == "AskUser":
            return 1.0  # High cost - requires user interaction
        else:
            return 0.1  # Low cost - internal processing
    
    def _calculate_entropy(self, state: AgentState) -> float:
        """Calculate entropy of current belief distribution."""
        if not state.belief_state.probs:
            return 0.0
            
        entropy = 0.0
        for prob in state.belief_state.probs.values():
            if prob > 0:
                entropy -= prob * math.log2(prob)
                
        return entropy
    
    async def _execute_action(self, action: Action, state: AgentState) -> Optional[Evidence]:
        """Execute an action and return any immediate evidence."""
        if action.type == "AskUser":
            # AskUser returns no immediate evidence - waits for user response
            return None
        elif action.type == "Hypothesize":
            return await self._execute_hypothesize(action, state)
        elif action.type == "ClusterThemes":
            return await self._execute_cluster_themes(action, state)
        elif action.type == "CounterfactualTest":
            return await self._execute_counterfactual_test(action, state)
        elif action.type == "EvidenceRequest":
            return await self._execute_evidence_request(action, state)
        elif action.type == "SilenceCheck":
            return await self._execute_silence_check(action, state)
        elif action.type == "ConfidenceUpdate":
            return await self._execute_confidence_update(action, state)
        else:
            # Unknown action type
            return None
    
    async def _execute_hypothesize(self, action: HypothesizeAction, state: AgentState) -> Evidence:
        """Generate new hypothesis nodes."""
        # For MVP, generate one additional hypothesis
        prompt = f"""
        Based on this journal entry and current hypotheses, suggest one additional potential root issue:
        
        Journal: {state.journal_entry.text[:500]}...
        
        Current hypotheses: {[node.text for node in state.belief_state.nodes]}
        
        Provide a new hypothesis that explores a different angle.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            new_hypothesis = response.choices[0].message.content or "Alternative perspective needed"
            
            # Add new node
            new_node = CruxNode(text=new_hypothesis[:400])
            state.belief_state.nodes.append(new_node)
            
            # Redistribute probabilities
            n = len(state.belief_state.nodes)
            for node in state.belief_state.nodes:
                state.belief_state.probs[node.node_id] = 1.0 / n
                
            # Update rankings
            state.belief_state.top_ids = list(state.belief_state.probs.keys())
            
            return Evidence(
                kind="PatternSignal",
                payload={"new_hypothesis": new_hypothesis},
                at_revision=state.revision
            )
            
        except Exception as e:
            logger.error(f"Failed to execute hypothesize: {e}")
            return Evidence(
                kind="PatternSignal",
                payload={"error": "Failed to generate new hypothesis"},
                at_revision=state.revision
            )
    
    async def _execute_cluster_themes(self, action: ClusterThemesAction, state: AgentState) -> Evidence:
        """Cluster similar themes and merge nodes."""
        # Simplified clustering for MVP - merge very similar nodes
        nodes_to_merge = []
        
        # Simple text similarity check
        for i, node1 in enumerate(state.belief_state.nodes):
            for j, node2 in enumerate(state.belief_state.nodes[i+1:], i+1):
                if self._text_similarity(node1.text, node2.text) > self.config.MERGE_RADIUS:
                    nodes_to_merge.append((node1, node2))
        
        merged_count = 0
        for node1, node2 in nodes_to_merge:
            if node1.status == "active" and node2.status == "active":
                # Merge node2 into node1
                node1.supports.extend(node2.supports)
                node1.counters.extend(node2.counters)
                node2.status = "merged"
                
                # Combine probabilities
                prob1 = state.belief_state.probs.get(node1.node_id, 0.0)
                prob2 = state.belief_state.probs.get(node2.node_id, 0.0)
                state.belief_state.probs[node1.node_id] = prob1 + prob2
                del state.belief_state.probs[node2.node_id]
                
                merged_count += 1
        
        # Update rankings
        active_nodes = [n for n in state.belief_state.nodes if n.status == "active"]
        state.belief_state.top_ids = sorted(
            [n.node_id for n in active_nodes],
            key=lambda nid: state.belief_state.probs.get(nid, 0.0),
            reverse=True
        )
        
        return Evidence(
            kind="PatternSignal",
            payload={"merged_nodes": merged_count},
            at_revision=state.revision
        )
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation."""
        # Very basic implementation - could use proper embeddings
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _execute_confidence_update(self, action: ConfidenceUpdateAction, state: AgentState) -> Evidence:
        """Update confidence scores based on accumulated evidence."""
        # Renormalize probabilities to ensure they sum to 1
        total_prob = sum(state.belief_state.probs.values())
        if total_prob > 0:
            for node_id in state.belief_state.probs:
                state.belief_state.probs[node_id] /= total_prob
        
        # Update rankings
        state.belief_state.top_ids = sorted(
            state.belief_state.probs.keys(),
            key=lambda nid: state.belief_state.probs.get(nid, 0.0),
            reverse=True
        )
        
        return Evidence(
            kind="ContextDatum",
            payload={"confidence_update": "normalized"},
            at_revision=state.revision
        )
    
    async def _execute_counterfactual_test(self, action: CounterfactualTestAction, state: AgentState) -> Evidence:
        """Execute counterfactual testing to differentiate persistent vs. situational drivers."""
        test_spec = action.test_spec
        test_type = test_spec.get("type", "temporal")
        
        if test_type == "temporal":
            # Test: "Would this issue exist if circumstances were different?"
            prompt = f"""
            Consider this journal entry: {state.journal_entry.text[:300]}...
            
            Current hypotheses about the core issue:
            {[node.text for node in state.belief_state.nodes if node.status == "active"][:3]}
            
            For each hypothesis, assess: Would this issue likely persist if:
            - The timing was different (different day/week/season)
            - The external circumstances changed
            - The person was in a different environment
            
            Provide a brief analysis of which factors seem persistent vs. situational.
            """
        else:
            # Generic counterfactual prompt
            prompt = f"""
            Analyze the core issue from this journal entry: {state.journal_entry.text[:300]}...
            
            Consider alternative scenarios where key variables are changed.
            What aspects would likely remain vs. change?
            """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            analysis = response.choices[0].message.content or "No clear counterfactual insights"
            
            return Evidence(
                kind="MicroExperimentResult",
                payload={
                    "test_type": test_type,
                    "analysis": analysis,
                    "persistent_factors": "extracted via analysis"  # Could be enhanced
                },
                at_revision=state.revision
            )
            
        except Exception as e:
            logger.error(f"Failed to execute counterfactual test: {e}")
            return Evidence(
                kind="MicroExperimentResult",
                payload={"error": "Failed to complete counterfactual analysis"},
                at_revision=state.revision
            )
    
    async def _execute_evidence_request(self, action: EvidenceRequestAction, state: AgentState) -> Evidence:
        """Request specific types of evidence to inform belief updates."""
        evidence_kind = action.kind
        
        if evidence_kind == "timeline":
            context_prompt = "When did this issue first appear? What events preceded it?"
        elif evidence_kind == "constraints":
            context_prompt = "What limitations or constraints are affecting this situation?"
        elif evidence_kind == "goals":
            context_prompt = "What are you trying to achieve? What outcomes do you want?"
        elif evidence_kind == "norms":
            context_prompt = "What expectations (yours or others') are involved in this situation?"
        else:
            context_prompt = "What additional context would help understand this better?"
        
        # For MVP, we simulate getting this evidence from the journal entry
        # In a full implementation, this might involve asking the user
        prompt = f"""
        Based on this journal entry: {state.journal_entry.text}
        
        Extract information relevant to: {context_prompt}
        
        Provide specific details if available, or note what information is missing.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            extracted_info = response.choices[0].message.content or f"No clear {evidence_kind} information"
            
            return Evidence(
                kind="ContextDatum",
                payload={
                    "evidence_type": evidence_kind,
                    "extracted_info": extracted_info,
                    "prompt_used": context_prompt
                },
                at_revision=state.revision
            )
            
        except Exception as e:
            logger.error(f"Failed to execute evidence request: {e}")
            return Evidence(
                kind="ContextDatum",
                payload={"error": f"Failed to extract {evidence_kind} evidence"},
                at_revision=state.revision
            )
    
    async def _execute_silence_check(self, action: SilenceCheckAction, state: AgentState) -> Evidence:
        """Check for what's not being said - important omissions or avoided topics."""
        
        prompt = f"""
        Analyze what might be missing or avoided in this journal entry: {state.journal_entry.text}
        
        Current focus areas: {[node.text for node in state.belief_state.nodes if node.status == "active"][:3]}
        
        Consider:
        - What emotions or feelings are not mentioned?
        - What relationships or people are notably absent?
        - What potential causes or solutions are not explored?
        - What fears or concerns might be unspoken?
        
        Identify 1-2 significant omissions that might be relevant to understanding the core issue.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            silence_analysis = response.choices[0].message.content or "No clear omissions detected"
            
            # Extract potential new hypothesis from silence analysis
            if "missing" in silence_analysis.lower() or "avoid" in silence_analysis.lower():
                # Could spawn a new hypothesis about the avoided topic
                potential_hypothesis = f"Avoidance or omission: {silence_analysis[:200]}..."
                
                # Add as a new node if it's substantive
                if len(potential_hypothesis) > 50:
                    new_node = CruxNode(text=potential_hypothesis[:400])
                    state.belief_state.nodes.append(new_node)
                    
                    # Assign initial probability
                    n_active = len([n for n in state.belief_state.nodes if n.status == "active"])
                    if n_active > 0:
                        # Redistribute probabilities
                        initial_prob = 0.1  # Conservative initial probability
                        for node_id in state.belief_state.probs:
                            state.belief_state.probs[node_id] *= (1.0 - initial_prob)
                        state.belief_state.probs[new_node.node_id] = initial_prob
            
            return Evidence(
                kind="PatternSignal",
                payload={
                    "silence_analysis": silence_analysis,
                    "omissions_detected": True if "missing" in silence_analysis.lower() else False
                },
                at_revision=state.revision
            )
            
        except Exception as e:
            logger.error(f"Failed to execute silence check: {e}")
            return Evidence(
                kind="PatternSignal",
                payload={"error": "Failed to analyze potential omissions"},
                at_revision=state.revision
            )
    
    async def _process_user_event(self, state: AgentState, user_event: Dict[str, Any]) -> None:
        """Process user response and update beliefs."""
        answer_to = user_event.get("answer_to")
        value = user_event.get("value", "")
        
        if not answer_to or not state.last_action:
            return
            
        if str(state.last_action.action_id) != str(answer_to):
            raise ValueError(f"User event answer_to {answer_to} does not match last action {state.last_action.action_id}")
        
        # Create evidence from user response
        evidence = Evidence(
            kind="UserAnswer",
            payload={"question": getattr(state.last_action, "question", ""), "answer": value},
            at_revision=state.revision
        )
        
        # Add to evidence log
        state.evidence_log.append(evidence)
        
        # Update beliefs based on response
        await self._update_beliefs(state, evidence)
    
    async def _update_beliefs(self, state: AgentState, evidence: Evidence) -> None:
        """Update belief probabilities based on new evidence."""
        if evidence.kind == "UserAnswer" and isinstance(state.last_action, AskUserAction):
            await self._update_beliefs_from_user_answer(state, evidence)
        else:
            # For other evidence types, minimal update for MVP
            logger.debug(f"Received evidence: {evidence.kind}")
    
    async def _update_beliefs_from_user_answer(self, state: AgentState, evidence: Evidence) -> None:
        """
        Update beliefs based on user's answer using log-odds space with bounded step size.
        
        Implements: Featureize observation vs. each node, update in log-odds space, 
        merge near-duplicates, retire dominated nodes.
        """
        if not isinstance(state.last_action, AskUserAction):
            return
            
        answer = evidence.payload.get("answer", "")
        targets = state.last_action.targets
        
        # Featurize the observation against each node
        node_features = self._featurize_observation(evidence, state.belief_state.nodes)
        
        # Update beliefs in log-odds space with bounded step size
        self._update_log_odds(state, node_features, targets, answer)
        
        # Merge near-duplicate nodes
        self._merge_similar_nodes(state)
        
        # Retire dominated nodes
        self._retire_dominated_nodes(state)
        
        # Update rankings
        self._update_rankings(state)
    
    def _featurize_observation(self, evidence: Evidence, nodes: List[CruxNode]) -> Dict[UUID, Dict[str, float]]:
        """
        Featurize observation vs. each node (entail/contradict, specificity, novelty).
        """
        features = {}
        answer = evidence.payload.get("answer", "").lower()
        
        for node in nodes:
            if node.status != "active":
                continue
                
            node_features = {
                "entailment": 0.0,     # How much the answer supports this node
                "contradiction": 0.0,  # How much the answer contradicts this node  
                "specificity": 0.0,    # How specific the answer is to this node
                "novelty": 0.0         # How novel this information is
            }
            
            # Simple keyword-based featurization (could be enhanced with embeddings)
            node_text_lower = node.text.lower()
            
            # Entailment: answer contains words from node text
            node_words = set(node_text_lower.split())
            answer_words = set(answer.split())
            overlap = len(node_words.intersection(answer_words))
            if len(node_words) > 0:
                node_features["entailment"] = overlap / len(node_words)
            
            # Specificity: how unique the overlap is
            if overlap > 0:
                node_features["specificity"] = overlap / len(answer_words) if len(answer_words) > 0 else 0.0
            
            # Novelty: based on existing supports/counters
            existing_evidence = len(node.supports) + len(node.counters)
            node_features["novelty"] = 1.0 / (1.0 + existing_evidence * 0.1)
            
            features[node.node_id] = node_features
            
        return features
    
    def _update_log_odds(self, state: AgentState, node_features: Dict[UUID, Dict[str, float]], 
                        targets: List[UUID], answer: str) -> None:
        """Update beliefs in log-odds space with bounded step size."""
        
        # Convert probabilities to log-odds
        log_odds = {}
        for node_id, prob in state.belief_state.probs.items():
            # Avoid log(0) by using small epsilon
            prob = max(prob, 1e-10)
            prob = min(prob, 1 - 1e-10)
            log_odds[node_id] = math.log(prob / (1 - prob))
        
        # Define step size bounds
        MAX_STEP_SIZE = 2.0
        MIN_STEP_SIZE = 0.1
        
        answer_lower = answer.lower()
        
        for node_id, features in node_features.items():
            if node_id not in log_odds:
                continue
                
            # Calculate update magnitude based on features
            update_strength = (
                features["entailment"] * 0.4 +
                features["specificity"] * 0.3 + 
                features["novelty"] * 0.3
            )
            
            # Determine update direction based on answer and targets
            update_direction = 0.0
            
            if node_id in targets:
                # This node was specifically being asked about
                if any(choice in answer_lower for choice in ["first", "option", "yes", "agree"]):
                    if targets.index(node_id) == 0:  # First target
                        update_direction = 1.0
                    elif len(targets) > 1 and targets.index(node_id) == 1:  # Second target
                        update_direction = -0.5  # Reduce confidence in first when second chosen
                elif any(choice in answer_lower for choice in ["second"]):
                    if targets.index(node_id) == 0:  # First target
                        update_direction = -0.5
                    elif len(targets) > 1 and targets.index(node_id) == 1:  # Second target  
                        update_direction = 1.0
                elif any(choice in answer_lower for choice in ["both", "equally"]):
                    update_direction = 0.3  # Slight boost to both
                elif any(choice in answer_lower for choice in ["neither", "no"]):
                    update_direction = -0.8  # Strong negative
            else:
                # Node not directly targeted - small indirect update based on entailment
                if features["entailment"] > 0.3:
                    update_direction = 0.2
                elif features["contradiction"] > 0.3:
                    update_direction = -0.2
            
            # Apply bounded step size
            step_size = update_strength * MAX_STEP_SIZE
            step_size = max(MIN_STEP_SIZE, min(MAX_STEP_SIZE, step_size))
            
            # Update log-odds
            log_odds[node_id] += update_direction * step_size
            
            # Bound log-odds to prevent extreme values
            log_odds[node_id] = max(-10.0, min(10.0, log_odds[node_id]))
        
        # Convert back to probabilities and renormalize
        new_probs = {}
        for node_id, lo in log_odds.items():
            new_probs[node_id] = 1.0 / (1.0 + math.exp(-lo))
        
        # Renormalize to sum to 1
        total = sum(new_probs.values())
        if total > 0:
            for node_id in new_probs:
                new_probs[node_id] /= total
        
        state.belief_state.probs = new_probs
    
    def _merge_similar_nodes(self, state: AgentState) -> None:
        """Merge near-duplicate nodes (cosine ≥ MERGE_RADIUS)."""
        nodes_to_merge = []
        active_nodes = [n for n in state.belief_state.nodes if n.status == "active"]
        
        for i, node1 in enumerate(active_nodes):
            for j, node2 in enumerate(active_nodes[i+1:], i+1):
                similarity = self._calculate_node_similarity(node1, node2)
                if similarity >= self.config.MERGE_RADIUS:
                    nodes_to_merge.append((node1, node2, similarity))
        
        # Sort by similarity (highest first) and merge
        nodes_to_merge.sort(key=lambda x: x[2], reverse=True)
        
        for node1, node2, similarity in nodes_to_merge:
            if node1.status == "active" and node2.status == "active":
                logger.debug(f"Merging nodes with similarity {similarity:.3f}")
                
                # Merge node2 into node1
                node1.supports.extend(node2.supports)
                node1.counters.extend(node2.counters)
                node1.text = f"{node1.text} / {node2.text}"[:400]  # Combined text, truncated
                node2.status = "merged"
                
                # Combine probabilities
                prob1 = state.belief_state.probs.get(node1.node_id, 0.0)
                prob2 = state.belief_state.probs.get(node2.node_id, 0.0)
                state.belief_state.probs[node1.node_id] = prob1 + prob2
                
                if node2.node_id in state.belief_state.probs:
                    del state.belief_state.probs[node2.node_id]
    
    def _calculate_node_similarity(self, node1: CruxNode, node2: CruxNode) -> float:
        """Calculate semantic similarity between two nodes (simple word overlap for MVP)."""
        words1 = set(node1.text.lower().split())
        words2 = set(node2.text.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _retire_dominated_nodes(self, state: AgentState) -> None:
        """Retire dominated nodes (low probability for K turns)."""
        K_TURNS_THRESHOLD = 3
        LOW_PROB_THRESHOLD = 0.05
        
        # Track how many turns each node has been below threshold
        if not hasattr(state, '_low_prob_counts'):
            state._low_prob_counts = {}
        
        for node in state.belief_state.nodes:
            if node.status != "active":
                continue
                
            current_prob = state.belief_state.probs.get(node.node_id, 0.0)
            
            if current_prob < LOW_PROB_THRESHOLD:
                state._low_prob_counts[node.node_id] = state._low_prob_counts.get(node.node_id, 0) + 1
                
                if state._low_prob_counts[node.node_id] >= K_TURNS_THRESHOLD:
                    logger.debug(f"Retiring dominated node: {node.text[:50]}...")
                    node.status = "retired"
                    if node.node_id in state.belief_state.probs:
                        del state.belief_state.probs[node.node_id]
            else:
                # Reset counter if probability recovers
                state._low_prob_counts[node.node_id] = 0
    
    def _update_rankings(self, state: AgentState) -> None:
        """Update node rankings based on current probabilities."""
        active_node_ids = [
            n.node_id for n in state.belief_state.nodes 
            if n.status == "active" and n.node_id in state.belief_state.probs
        ]
        
        state.belief_state.top_ids = sorted(
            active_node_ids,
            key=lambda nid: state.belief_state.probs.get(nid, 0.0),
            reverse=True
        )
    
    async def _finalize(self, state: AgentState, exit_reason: str) -> AgentResult:
        """Finalize the session and return the confirmed crux."""
        
        # Calculate entropy reduction for observability
        initial_entropy = 0.0  # Would need to track from start in production
        final_entropy = self._calculate_entropy(state)
        entropy_reduction = max(0.0, initial_entropy - final_entropy)
        
        # Track completion
        self.observability.track_completion(exit_reason, entropy_reduction)
        
        # Select top hypothesis as confirmed crux
        if state.belief_state.top_ids and state.belief_state.probs:
            top_id = state.belief_state.top_ids[0]
            top_node = next((n for n in state.belief_state.nodes if n.node_id == top_id), None)
            
            if top_node:
                confirmed_crux = ConfirmedCruxV3(
                    node_id=top_id,
                    text=top_node.text,
                    confidence=state.belief_state.probs.get(top_id, 0.0)
                )
                
                # Collect secondary themes
                secondary_themes = []
                for node_id in state.belief_state.top_ids[1:]:
                    node = next((n for n in state.belief_state.nodes if n.node_id == node_id), None)
                    if node and state.belief_state.probs.get(node_id, 0.0) > 0.1:
                        secondary_themes.append(SecondaryThemeV3(
                            node_id=node_id,
                            text=node.text,
                            confidence=state.belief_state.probs.get(node_id, 0.0)
                        ))
                
                # Generate reasoning trail
                reasoning_trail = self._generate_reasoning_trail(state)
                
                return AgentResult(
                    confirmed_crux=confirmed_crux,
                    secondary_themes=secondary_themes,
                    reasoning_trail=reasoning_trail,
                    exit_reason=exit_reason
                )
        
        # Fallback if no valid crux found
        fallback_crux = ConfirmedCruxV3(
            node_id=uuid4(),
            text="Core challenge requiring further exploration",
            confidence=0.5
        )
        
        return AgentResult(
            confirmed_crux=fallback_crux,
            secondary_themes=[],
            reasoning_trail="Session ended without clear crux identification.",
            exit_reason=exit_reason
        )
    
    def _generate_reasoning_trail(self, state: AgentState) -> str:
        """Generate a narrative reasoning trail of the discovery process."""
        trail_parts = []
        
        trail_parts.append(f"FACD session completed after {state.revision} steps, using {state.budget_used} user queries.")
        
        if state.belief_state.nodes:
            trail_parts.append(f"Explored {len(state.belief_state.nodes)} hypotheses:")
            for i, node in enumerate(state.belief_state.nodes[:3]):  # Top 3
                confidence = state.belief_state.probs.get(node.node_id, 0.0)
                trail_parts.append(f"  {i+1}. {node.text} (confidence: {confidence:.2f})")
        
        if state.evidence_log:
            trail_parts.append(f"Collected {len(state.evidence_log)} pieces of evidence through user interactions.")
        
        return " ".join(trail_parts)
    
    async def _finalize_with_crisis_intervention(self, state: AgentState) -> AgentResult:
        """Finalize session with crisis intervention triggered."""
        
        # Track crisis intervention
        entropy_reduction = 0.0  # No meaningful entropy reduction in crisis
        self.observability.track_completion("guardrail", entropy_reduction)
        
        # Create a crisis-specific confirmed crux
        crisis_crux = ConfirmedCruxV3(
            node_id=uuid4(),
            text="Crisis or distress requiring immediate support and professional help",
            confidence=1.0
        )
        
        # Generate reasoning trail for crisis intervention
        reasoning_trail = f"FACD session terminated early due to distress indicators detected. Crisis intervention protocols activated. Session duration: {state.revision} steps."
        
        # Add crisis resources to the result
        crisis_resources = self.guardrails.get_crisis_resources()
        
        return AgentResult(
            confirmed_crux=crisis_crux,
            secondary_themes=[],
            reasoning_trail=f"{reasoning_trail} Crisis resources: {crisis_resources}",
            exit_reason="guardrail"
        )
    
    def _compute_integrity(self, state: AgentState) -> str:
        """Compute HMAC integrity signature for state."""
        # Create a canonical representation excluding the integrity field
        state_dict = state.model_dump(exclude={"integrity"})
        state_json = str(sorted(state_dict.items()))
        
        signature = hmac.new(
            self.secret_key.encode(),
            state_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_integrity(self, state: AgentState) -> bool:
        """Verify HMAC integrity signature."""
        if not state.integrity:
            return True  # No signature to verify
            
        expected = self._compute_integrity(state)
        return hmac.compare_digest(state.integrity, expected)
    
    def get_observability_stats(self) -> Dict[str, Any]:
        """Get current observability statistics."""
        return self.observability.get_summary_stats()