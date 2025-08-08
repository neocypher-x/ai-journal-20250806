"""
AI agents for the journal reflection system.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
import logging

from .config import get_openai_client, settings
from .models import IngestResult, AgentInsight, AgentCallResult
from .logging_config import log_agent_call


class BaseAgent:
    """Base class for all AI agents."""
    
    def __init__(self, name: str, model: str = None):
        self.name = name
        self.model = model or settings.COACH_MODEL
        self.client = get_openai_client()
        self.logger = logging.getLogger(f"ai_journal.agents.{name}")
    
    async def _call_openai(self, messages: list, response_format: dict = None, 
                          max_tokens: int = None) -> Dict[str, Any]:
        """Make an OpenAI API call with error handling."""
        try:
            call_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": settings.TEMPERATURE,
                "max_tokens": max_tokens or settings.MAX_TOKENS_PER_REQUEST,
            }
            
            if response_format:
                call_kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**call_kwargs)
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "model": response.model
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    async def call_with_timeout(self, *args, **kwargs) -> AgentCallResult:
        """Call the agent with timeout and result tracking."""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.process(*args, **kwargs),
                timeout=settings.AGENT_TIMEOUT_SEC
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            tokens_used = getattr(result, 'tokens_used', 0) if hasattr(result, 'tokens_used') else 0
            
            log_agent_call(
                self.name, 
                kwargs.get('trace_id', 'unknown'),
                True, 
                duration_ms, 
                tokens_used
            )
            
            return AgentCallResult(
                agent_name=self.name,
                success=True,
                result=result.dict() if hasattr(result, 'dict') else result,
                duration_ms=duration_ms,
                tokens_used=tokens_used
            )
            
        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Agent {self.name} timed out after {settings.AGENT_TIMEOUT_SEC}s"
            
            log_agent_call(
                self.name,
                kwargs.get('trace_id', 'unknown'),
                False,
                duration_ms,
                error=error_msg
            )
            
            return AgentCallResult(
                agent_name=self.name,
                success=False,
                error=error_msg,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Agent {self.name} failed: {str(e)}"
            
            log_agent_call(
                self.name,
                kwargs.get('trace_id', 'unknown'),
                False,
                duration_ms,
                error=error_msg
            )
            
            return AgentCallResult(
                agent_name=self.name,
                success=False,
                error=error_msg,
                duration_ms=duration_ms
            )


class JournalIngestorAgent(BaseAgent):
    """Agent responsible for ingesting and analyzing journal entries."""
    
    def __init__(self):
        super().__init__("journal_ingestor", settings.INGESTOR_MODEL)
    
    async def process(self, journal_text: str, trace_id: str) -> IngestResult:
        """Process journal text and extract summary, themes, and mood."""
        
        system_prompt = """You are a journal analysis expert. Your task is to analyze journal entries and extract key information.

You must respond with valid JSON in exactly this format:
{
    "summary": "A concise summary in 120 words or less",
    "themes": ["theme1", "theme2", "theme3"],
    "mood": "one of: calm, tense, stressed, sad, angry, energized, mixed"
}

Guidelines:
- Summary: Capture the main points and experiences described
- Themes: Identify 1-5 key themes or topics (e.g., "relationships", "work stress", "personal growth")
- Mood: Select the single best mood that reflects the overall emotional tone
- Be objective and factual, avoid interpretation or advice"""

        user_prompt = f"""Please analyze this journal entry:

{journal_text}

Respond with the required JSON format only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {
            "type": "json_object"
        }
        
        result = await self._call_openai(messages, response_format, max_tokens=1000)
        
        try:
            parsed_result = json.loads(result["content"])
            ingest_result = IngestResult(**parsed_result)
            print("tokens_used", result["tokens_used"])  # Add for tracking
            return ingest_result
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse ingestor result: {e}")
            self.logger.error(f"Raw response: {result['content']}")
            raise ValueError(f"Invalid response format from journal ingestor: {e}")


class PhilosophyCoachAgent(BaseAgent):
    """Base class for philosophy-specific coaching agents."""
    
    def __init__(self, philosophy_name: str, philosophy_principles: str):
        super().__init__(f"{philosophy_name.lower()}_coach")
        self.philosophy_name = philosophy_name
        self.philosophy_principles = philosophy_principles
    
    async def process(self, summary: str, themes: list, mood: str, 
                     question: str = None, trace_id: str = None) -> AgentInsight:
        """Generate philosophical insights and prompts."""
        
        system_prompt = f"""You are a {self.philosophy_name} philosophy coach. Your expertise is in applying {self.philosophy_name} principles to personal reflection and growth.

Core principles of {self.philosophy_name}:
{self.philosophy_principles}

Your task is to provide practical insights and actionable reflection prompts based on the journal content. Focus on what can be practically applied, not abstract theory.

Respond with valid JSON in this format:
{{
    "insights": ["practical insight 1", "practical insight 2"],
    "prompt_suggestions": ["actionable reflection prompt 1", "actionable reflection prompt 2"],
    "caveats": ["optional caveat or consideration"]
}}

Guidelines:
- Insights: 1-3 practical observations from a {self.philosophy_name} perspective
- Prompt suggestions: 1-3 actionable questions or exercises for reflection
- Caveats: Optional warnings or considerations (can be empty array)
- Keep prompts specific and actionable, starting with verbs when possible
- Ground advice in real-world application, not philosophical abstractions"""

        context_parts = [
            f"Journal summary: {summary}",
            f"Key themes: {', '.join(themes)}",
            f"Current mood: {mood}"
        ]
        
        if question:
            context_parts.append(f"Specific question: {question}")
        
        user_prompt = f"""Based on this journal context:

{chr(10).join(context_parts)}

Please provide {self.philosophy_name} insights and reflection prompts."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {
            "type": "json_object"
        }
        
        result = await self._call_openai(messages, response_format, max_tokens=800)
        
        try:
            parsed_result = json.loads(result["content"])
            insight = AgentInsight(**parsed_result)
            print("tokens_used", result["tokens_used"])  # Add for tracking
            return insight
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse {self.name} result: {e}")
            self.logger.error(f"Raw response: {result['content']}")
            raise ValueError(f"Invalid response format from {self.name}: {e}")


class BuddhistCoachAgent(PhilosophyCoachAgent):
    """Buddhist philosophy coach agent."""
    
    def __init__(self):
        principles = """
- Mindfulness and present-moment awareness
- Understanding the impermanence of all experiences
- Compassion for self and others
- Recognition of interconnectedness
- The Middle Way - avoiding extremes
- Acceptance of suffering as part of the human condition
- Non-attachment to outcomes
- Cultivating wisdom through observation and reflection
"""
        super().__init__("Buddhist", principles)


class StoicCoachAgent(PhilosophyCoachAgent):
    """Stoic philosophy coach agent."""
    
    def __init__(self):
        principles = """
- Focus on what is within your control vs. what is not
- Virtue as the highest good (wisdom, justice, courage, temperance)
- Accepting what you cannot change with equanimity
- Taking responsibility for your thoughts and actions
- Living according to nature and reason
- Emotional resilience through rational thinking
- The discipline of desire, action, and assent
- Viewing obstacles as opportunities for growth
"""
        super().__init__("Stoic", principles)


class ExistentialistCoachAgent(PhilosophyCoachAgent):
    """Existentialist philosophy coach agent."""
    
    def __init__(self):
        principles = """
- Personal freedom and responsibility for creating meaning
- Authenticity - being true to your own values and choices
- Confronting anxiety and uncertainty as part of human existence
- The importance of individual experience and subjectivity
- Creating your own essence through choices and actions
- Embracing the burden and freedom of self-determination
- Finding meaning in the face of life's apparent absurdity
- Taking ownership of your decisions and their consequences
"""
        super().__init__("Existentialist", principles)