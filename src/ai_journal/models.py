"""
Pydantic models for the AI Journal Reflection System.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
import uuid
from datetime import datetime


Mood = Literal["calm", "tense", "stressed", "sad", "angry", "energized", "mixed"]
PhilosophySource = Literal["buddhist", "stoic", "existential"]


class ReflectRequest(BaseModel):
    """Request model for the /reflect endpoint."""
    journal_text: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="The journal entry text to analyze (300-1000 words typical)"
    )
    question: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional specific question about the journal content"
    )

    @validator('journal_text')
    def validate_journal_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Journal text cannot be empty")
        return v.strip()


class IngestResult(BaseModel):
    """Model for journal ingestor agent output."""
    summary: str = Field(
        ...,
        max_length=1000,
        description="Concise summary of the journal entry (<=120 words)"
    )
    themes: List[str] = Field(
        ...,
        max_items=5,
        min_items=1,
        description="Key themes extracted from the journal (max 5)"
    )
    mood: Mood = Field(
        ...,
        description="Detected mood/emotional state"
    )

    @validator('themes')
    def validate_themes(cls, v):
        if not v:
            raise ValueError("At least one theme must be identified")
        return [theme.strip() for theme in v if theme.strip()]


class AgentInsight(BaseModel):
    """Model for philosophy coach agent output."""
    insights: List[str] = Field(
        ...,
        max_items=3,
        min_items=1,
        description="Key philosophical insights (max 3)"
    )
    prompt_suggestions: List[str] = Field(
        ...,
        max_items=3,
        min_items=1,
        description="Actionable reflection prompt suggestions (max 3)"
    )
    caveats: Optional[List[str]] = Field(
        None,
        max_items=2,
        description="Optional caveats or considerations"
    )

    @validator('insights', 'prompt_suggestions')
    def validate_non_empty_lists(cls, v):
        if not v or not any(item.strip() for item in v):
            raise ValueError("List cannot be empty or contain only whitespace")
        return [item.strip() for item in v if item.strip()]


class PromptItem(BaseModel):
    """Model for a single reflection prompt."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The actionable reflection prompt"
    )
    source: PhilosophySource = Field(
        ...,
        description="Philosophy tradition source"
    )
    rationale: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Brief explanation for why this prompt is relevant"
    )

    @validator('text')
    def validate_prompt_actionability(cls, v):
        if not v.strip():
            raise ValueError("Prompt text cannot be empty")
        # Check for actionable language
        action_words = ['consider', 'reflect', 'ask', 'examine', 'explore', 'practice', 'try', 'notice', 'observe']
        if not any(word in v.lower() for word in action_words):
            # Still allow it, but log a warning in production
            pass
        return v.strip()


class ReflectResponse(BaseModel):
    """Response model for the /reflect endpoint."""
    summary: str = Field(
        ...,
        description="Summary of the journal entry"
    )
    themes: List[str] = Field(
        ...,
        description="Key themes identified"
    )
    mood: Mood = Field(
        ...,
        description="Detected mood"
    )
    prompts: List[PromptItem] = Field(
        ...,
        max_items=5,
        min_items=1,
        description="Reflection prompts (max 5)"
    )
    advice: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Brief, concrete guidance (<=120 words typical)"
    )
    warnings: Optional[List[str]] = Field(
        None,
        description="Any warnings or issues during processing"
    )
    trace_id: str = Field(
        ...,
        description="Unique identifier for request tracing"
    )
    processed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the request was processed"
    )

    @validator('prompts')
    def validate_prompts_balance(cls, v):
        if not v:
            raise ValueError("At least one prompt is required")
        
        # Check source balance (max 2 per source)
        source_counts = {}
        for prompt in v:
            source_counts[prompt.source] = source_counts.get(prompt.source, 0) + 1
            if source_counts[prompt.source] > 2:
                raise ValueError(f"Too many prompts from {prompt.source} source (max 2)")
        
        return v


class AgentCallResult(BaseModel):
    """Internal model for tracking agent call results."""
    agent_name: str
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None

    class Config:
        # Allow arbitrary types for flexibility
        arbitrary_types_allowed = True


class ProcessingContext(BaseModel):
    """Internal model for passing context between processing stages."""
    trace_id: str
    request: ReflectRequest
    ingest_result: Optional[IngestResult] = None
    agent_results: List[AgentCallResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True