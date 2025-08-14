"""
Orchestration service for coordinating philosophical agents and generating reflections.
"""

import asyncio
from typing import List
from openai import AsyncOpenAI

from ai_journal.models import JournalEntry, Reflection, Perspectives, ReflectionRequest
from ai_journal.agents import BuddhistAgent, StoicAgent, ExistentialistAgent, NeoAdlerianAgent, ScoutAgent
from ai_journal.oracle import OracleAgent


class ReflectionService:
    """Service that coordinates all agents to generate philosophical reflections."""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        
        # Initialize agents
        self.buddhist_agent = BuddhistAgent(self.client, self.model)
        self.stoic_agent = StoicAgent(self.client, self.model)
        self.existentialist_agent = ExistentialistAgent(self.client, self.model)
        self.neoadlerian_agent = NeoAdlerianAgent(self.client, self.model)
        self.scout_agent = ScoutAgent(self.client, self.model)
        self.oracle_agent = OracleAgent(self.client, self.model)
    
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
    
    async def close(self):
        """Clean up resources."""
        await self.client.close()