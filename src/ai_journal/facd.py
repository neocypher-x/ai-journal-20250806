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
            
        # Check stop conditions
        exit_reason = self._should_stop(state)
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
    
    async def _enumerate_actions(self, state: AgentState) -> List[Action]:
        """Enumerate possible actions for current state."""
        actions = []
        
        # Always include AskUser unless budget exhausted
        if state.budget_used < self.config.MAX_USER_QUERIES:
            actions.append(self._create_ask_user_action(state))
            
        # Include Hypothesize if entropy is high
        if self._calculate_entropy(state) > 1.0:
            actions.append(HypothesizeAction(spawn_k=1))
            
        # Include clustering if many nodes
        if len(state.belief_state.nodes) >= 3:
            actions.append(ClusterThemesAction())
            
        # Include confidence update
        actions.append(ConfidenceUpdateAction())
        
        # Include stop if no budget
        if state.budget_used >= self.config.MAX_USER_QUERIES:
            actions.append(StopAction(exit_reason="budget"))
            
        return actions
    
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
        """Score actions by expected information gain minus cost."""
        scored = []
        
        for action in actions:
            # Simplified EVI calculation for MVP
            evi = await self._estimate_evi(action, state)
            cost = self._action_cost(action)
            score = evi - self.config.LAMBDA_COST * cost
            scored.append((action, score))
            
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    async def _estimate_evi(self, action: Action, state: AgentState) -> float:
        """Estimate expected information gain for an action."""
        # Simplified EVI calculation for MVP
        current_entropy = self._calculate_entropy(state)
        
        if action.type == "AskUser":
            # AskUser has high potential information gain
            return current_entropy * 0.5
        elif action.type == "Hypothesize":
            # Hypothesize can add new information but lower certainty
            return current_entropy * 0.3
        elif action.type == "ConfidenceUpdate":
            # Update can refine but not add new info
            return current_entropy * 0.1
        else:
            return current_entropy * 0.2
    
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
        elif action.type == "ConfidenceUpdate":
            return await self._execute_confidence_update(action, state)
        else:
            # Other actions return no evidence for now
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
        """Update beliefs based on user's answer to a question."""
        if not isinstance(state.last_action, AskUserAction):
            return
            
        answer = evidence.payload.get("answer", "")
        targets = state.last_action.targets
        
        # Simple belief update based on answer
        if "first" in answer.lower() or "option" in answer.lower():
            # User chose first option - boost first target
            if targets and len(targets) >= 1:
                target_id = targets[0]
                if target_id in state.belief_state.probs:
                    state.belief_state.probs[target_id] *= 1.5
        elif "second" in answer.lower():
            # User chose second option - boost second target
            if targets and len(targets) >= 2:
                target_id = targets[1]
                if target_id in state.belief_state.probs:
                    state.belief_state.probs[target_id] *= 1.5
        elif "neither" in answer.lower():
            # User rejected both - reduce target probabilities
            for target_id in targets:
                if target_id in state.belief_state.probs:
                    state.belief_state.probs[target_id] *= 0.7
        
        # Renormalize probabilities
        total = sum(state.belief_state.probs.values())
        if total > 0:
            for node_id in state.belief_state.probs:
                state.belief_state.probs[node_id] /= total
                
        # Update rankings
        state.belief_state.top_ids = sorted(
            state.belief_state.probs.keys(),
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