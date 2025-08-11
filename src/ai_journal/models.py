"""
Pydantic models for the AI Journal system.
"""

from enum import StrEnum, auto
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class Framework(StrEnum):
    BUDDHISM = auto()
    STOICISM = auto()
    EXISTENTIALISM = auto()
    NEOADLERIANISM = auto()
    OTHER = auto()  # used when proposed by Scout or user-defined


class AgreementStance(StrEnum):
    AGREE = auto()
    DIVERGE = auto()
    NUANCED = auto()


class JournalEntry(BaseModel):
    text: str = Field(min_length=1)  # 300–1000 words typical


# ---- Perspective -------------------------------------------------------------

class Perspective(BaseModel):
    """
    Output from a single framework for one journal entry.
    """
    framework: Framework
    # Required if framework == OTHER (proposed by Scout or custom name)
    other_framework_name: Optional[str] = Field(
        default=None,
        description="Name of the proposed/extra framework when framework=OTHER.",
        examples=["Confucianism", "ACT", "Taoism", "Adlerian Psychology"],
    )

    # Output elements (MVP structure) 
    core_principle_invoked: str = Field(
        description="1–2 sentence distillation of doctrine relevance.",
        min_length=1,
        max_length=600,
        examples=["This reflects impermanence (anicca) and non-grasping."],
    )
    challenge_framing: str = Field(
        description="Short, provocative reframe.",
        min_length=1,
        max_length=300,
        examples=["You are clinging to the illusion of control."],
    )
    practical_experiment: str = Field(
        description="One concrete action to try within ~24 hours.",
        min_length=1,
        max_length=800,
        examples=["Journal one thing you fear losing and reframe it as impermanent."],
    )
    potential_trap: str = Field(
        description="Common misuse warning.",
        min_length=1,
        max_length=600,
        examples=["Beware treating non-attachment as avoidance."],
    )
    key_metaphor: str = Field(
        description="Vivid one-liner aligned to tradition.",
        min_length=1,
        max_length=300,
        examples=["Like a sailor adjusting sails to the wind…"],
    )

    @model_validator(mode="after")
    def _check_other_framework(self):
        if self.framework == Framework.OTHER and not self.other_framework_name:
            raise ValueError("other_framework_name is required when framework=OTHER.")
        return self


class Perspectives(BaseModel):
    """
    Collection of per-framework perspectives for a single session.
    """
    items: List[Perspective] = Field(default_factory=list)


# ---- Prophecy (Oracle meta-analysis) ----------------------------------------

class AgreementItem(BaseModel):
    """
    Pairwise stance between two frameworks.
    """
    framework_a: Framework
    framework_b: Framework
    stance: AgreementStance
    notes: Optional[str] = Field(
        default=None,
        description="Optional short note clarifying stance.",
        max_length=600,
    )

    @model_validator(mode="after")
    def _normalize_pair(self):
        if self.framework_a == self.framework_b:
            raise ValueError("framework_a and framework_b must be different.")
        # normalize so (A,B) and (B,A) are identical
        if self.framework_a.name > self.framework_b.name:
            self.framework_a, self.framework_b = self.framework_b, self.framework_a
        return self


class AgreementScorecardResponse(BaseModel):
    """
    Structured response for agreement scorecard generation.
    """
    agreements: List[AgreementItem] = Field(
        description="List of pairwise framework agreement assessments"
    )


class TensionPoint(BaseModel):
    """
    Why frameworks diverge (or appear to).
    """
    frameworks: List[Framework] = Field(
        description="Usually a pair, but allow 2+ for broader tensions.",
        min_items=2,
    )
    explanation: str = Field(
        description="Text citing core principles driving the tension.",
        min_length=1,
        max_length=10000,
    )


class Prophecy(BaseModel):
    """
    Cross-framework meta-analysis and synthesis from the Oracle.
    """
    agreement_scorecard: List[AgreementItem] = Field(
        description="Pairwise Agree/Diverge/Nuanced marks."
    )
    tension_summary: List[TensionPoint] = Field(
        description="Explanations of divergence and their philosophical/psychological basis."
    )
    synthesis: str = Field(
        description="Unified principle or plan respecting all perspectives.",
        min_length=1,
        max_length=10000,
    )
    what_is_lost_by_blending: List[str] = Field(
        description="Explicit bullets of richness forfeited by compromise.",
        min_items=0,
        default_factory=list,
        examples=[["Buddhist emphasis on impermanence is softened.",
                   "Existential urgency reduced in favor of Stoic steadiness."]],
    )


# ---- Top-level Reflection ----------------------------------------------------

class Reflection(BaseModel):
    """
    Final system output for a single journal entry: perspectives + prophecy. 
    """
    journal_entry: JournalEntry
    perspectives: Perspectives
    prophecy: Prophecy


# ---- Structured Output Models for Oracle Agent -----------------------------

class TensionAnalysisResponse(BaseModel):
    """
    Structured response for tension analysis.
    """
    tension_points: List[TensionPoint] = Field(
        description="List of identified philosophical tensions",
        min_items=1,
        max_items=3
    )


class SynthesisResponse(BaseModel):
    """
    Structured response for synthesis generation.
    """
    synthesis: str = Field(
        description="Unified principle or plan respecting all perspectives",
        min_length=1,
        max_length=10000
    )


class WhatIsLostResponse(BaseModel):
    """
    Structured response for what is lost analysis.
    """
    lost_elements: List[str] = Field(
        description="Specific qualities lost or diminished in synthesis",
        min_items=1,
        max_items=5
    )


# ---- API-facing request/response (MVP CLI/API) ------------------------------

class ReflectionRequest(BaseModel):
    """
    Stateless processing request.
    """
    journal_entry: JournalEntry
    enable_scout: bool = Field(
        default=False,
        description=(
            "If true, allow an additional OTHER framework Perspective proposed "
            "by a Scout agent (can be philosophical or psychological)."
        ),
    )


class ReflectionResponse(BaseModel):
    """
    Response envelope for the generated reflection.
    """
    reflection: Reflection