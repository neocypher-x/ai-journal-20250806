"""
Orchestration service for coordinating philosophical agents and generating reflections.
"""

import asyncio
from typing import List, Union
from uuid import UUID
from openai import AsyncOpenAI

from ai_journal.models import (
    JournalEntry, Reflection, Perspectives, ReflectionRequest,
    # v2 models
    ExcavationInitRequest, ExcavationStepRequest, ExcavationStepResponse,
    ExcavationState, ExcavationResult, ReflectionRequestV2, ProbeTurn
)
from ai_journal.agents import BuddhistAgent, StoicAgent, ExistentialistAgent, NeoAdlerianAgent, ScoutAgent
from ai_journal.oracle import OracleAgent
from ai_journal.excavation import ExcavationEngine
from ai_journal.config import Settings


class ReflectionService:
    """Service that coordinates all agents to generate philosophical reflections."""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini", settings: Settings = None):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.settings = settings or Settings()
        
        # Initialize agents
        self.buddhist_agent = BuddhistAgent(self.client, self.model)
        self.stoic_agent = StoicAgent(self.client, self.model)
        self.existentialist_agent = ExistentialistAgent(self.client, self.model)
        self.neoadlerian_agent = NeoAdlerianAgent(self.client, self.model)
        self.scout_agent = ScoutAgent(self.client, self.model)
        self.oracle_agent = OracleAgent(self.client, self.model)
        
        # v2 excavation engine
        self.excavation_engine = ExcavationEngine(self.client, self.settings)
    
    async def generate_reflection(self, request: ReflectionRequest) -> Reflection:
        """Generate a complete philosophical reflection for a journal entry."""
        
        journal_entry = request.journal_entry
        
        # Step 1: Generate core perspectives concurrently
        perspective_tasks = [
            self.buddhist_agent.generate_perspective(journal_entry),
            self.stoic_agent.generate_perspective(journal_entry),
            self.existentialist_agent.generate_perspective(journal_entry),
            self.neoadlerian_agent.generate_perspective(journal_entry)
        ]
        
        core_perspectives = await asyncio.gather(*perspective_tasks)
        
        # Step 2: Optionally add Philosophy Scout perspective
        all_perspectives = list(core_perspectives)
        
        if request.enable_scout:
            scout_framework = await self.scout_agent.scout_relevant_framework(journal_entry)
            if scout_framework:
                scout_perspective = await self.scout_agent.generate_other_perspective(
                    journal_entry, scout_framework
                )
                all_perspectives.append(scout_perspective)
        
        perspectives = Perspectives(items=all_perspectives)
        
        # Step 3: Generate Oracle prophecy
        prophecy = await self.oracle_agent.generate_prophecy(perspectives)
        
        # Step 4: Assemble final reflection
        reflection = Reflection(
            journal_entry=journal_entry,
            perspectives=perspectives,
            prophecy=prophecy
        )
        
        return reflection
    
    # ---- v2 Excavation Methods ----
    
    async def process_excavation_step(self, request: Union[ExcavationInitRequest, ExcavationStepRequest]) -> ExcavationStepResponse:
        """Process a single excavation step (init or continue)."""
        
        if request.mode == "init":
            return await self._init_excavation(request)
        elif request.mode == "continue":
            return await self._continue_excavation(request)
        else:
            raise ValueError(f"Unknown excavation mode: {request.mode}")
    
    async def _init_excavation(self, request: ExcavationInitRequest) -> ExcavationStepResponse:
        """Initialize a new excavation."""
        
        # Seed initial hypotheses
        hypotheses = await self.excavation_engine.seed_hypotheses(request.journal_entry)
        
        # Create initial state
        state = ExcavationState(
            journal_entry=request.journal_entry,
            hypotheses=hypotheses,
            budget_used=0,
            revision=0
        )
        
        # Generate first probe
        probe = await self.excavation_engine.plan_next_probe(state)
        state.last_probe = probe
        state.revision = 1
        
        return ExcavationStepResponse(
            complete=False,
            state=state,
            next_probe=probe
        )
    
    async def _continue_excavation(self, request: ExcavationStepRequest) -> ExcavationStepResponse:
        """Continue an existing excavation."""
        
        state = request.state
        
        # Validate probe ID matches
        if not state.last_probe or state.last_probe.probe_id != request.expected_probe_id:
            raise ValueError("Probe ID mismatch - stale state or tampering detected")
        
        # Update beliefs based on user reply
        updated_hypotheses = await self.excavation_engine.update_beliefs(state, request.user_reply)
        
        # Record the turn
        probe_turn = ProbeTurn(
            probe=state.last_probe,
            user_reply=request.user_reply,
            updated_hypotheses=updated_hypotheses
        )
        
        # Update state
        state.hypotheses = updated_hypotheses
        state.probes_log.append(probe_turn)
        state.budget_used += 1
        state.revision += 1
        
        # Check exit conditions
        exit_result = self.excavation_engine.check_exit_conditions(updated_hypotheses, state.budget_used)
        
        if exit_result:
            exit_reason, excavation_result = exit_result
            state.exit_flags = {
                "passed_threshold": exit_reason == "threshold",
                "passed_confirmations": exit_reason == "confirmations", 
                "budget_exhausted": exit_reason == "budget"
            }
            
            return ExcavationStepResponse(
                complete=True,
                state=state,
                exit_reason=exit_reason,
                result=excavation_result
            )
        else:
            # Continue - generate next probe
            next_probe = await self.excavation_engine.plan_next_probe(state)
            state.last_probe = next_probe
            
            return ExcavationStepResponse(
                complete=False,
                state=state,
                next_probe=next_probe
            )
    
    async def generate_reflection_v2(self, request: ReflectionRequestV2) -> Reflection:
        """Generate a reflection from a completed excavation result."""
        
        excavation_result = request.from_excavation
        
        # Use the original journal entry if provided, otherwise reconstruct from crux
        if request.journal_entry:
            journal_entry = request.journal_entry
        else:
            # Reconstruct a minimal journal entry for the agents
            journal_entry = JournalEntry(
                text=f"Core issue identified: {excavation_result.confirmed_crux.text}"
            )
        
        # Create a synthetic journal entry that includes the crux and themes for the agents
        enhanced_text = f"""
        {journal_entry.text}
        
        [Analysis Context - Core Issue]: {excavation_result.confirmed_crux.text}
        """
        
        if excavation_result.secondary_themes:
            themes_text = ", ".join([theme.text for theme in excavation_result.secondary_themes])
            enhanced_text += f"\n[Secondary Themes]: {themes_text}"
        
        enhanced_entry = JournalEntry(text=enhanced_text)
        
        # Generate perspectives using the enhanced context
        perspective_tasks = [
            self.buddhist_agent.generate_perspective(enhanced_entry),
            self.stoic_agent.generate_perspective(enhanced_entry),
            self.existentialist_agent.generate_perspective(enhanced_entry),
            self.neoadlerian_agent.generate_perspective(enhanced_entry)
        ]
        
        core_perspectives = await asyncio.gather(*perspective_tasks)
        
        # Step 2: Optionally add Philosophy Scout perspective
        all_perspectives = list(core_perspectives)
        
        if request.enable_scout:
            scout_framework = await self.scout_agent.scout_relevant_framework(enhanced_entry)
            if scout_framework:
                scout_perspective = await self.scout_agent.generate_other_perspective(
                    enhanced_entry, scout_framework
                )
                all_perspectives.append(scout_perspective)
        
        perspectives = Perspectives(items=all_perspectives)
        
        # Step 3: Generate Oracle prophecy
        prophecy = await self.oracle_agent.generate_prophecy(perspectives)
        
        # Step 4: Assemble final reflection with original journal entry
        reflection = Reflection(
            journal_entry=journal_entry,  # Use original, not enhanced
            perspectives=perspectives,
            prophecy=prophecy
        )
        
        return reflection
    
    async def close(self):
        """Clean up resources."""
        await self.client.close()