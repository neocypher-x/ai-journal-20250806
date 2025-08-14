"""
Pydantic models for the AI Journal system.
"""

from enum import StrEnum, auto
from typing import List, Optional, Dict, Literal, Union, Any, Annotated
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, constr, conint


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


# ---- v2 Excavation Models ---------------------------------------------------

class CruxHypothesis(BaseModel):
    """
    A candidate statement representing a potential root issue in the journal entry.
    """
    hypothesis_id: UUID = Field(default_factory=uuid4)
    text: str = Field(min_length=1, max_length=400, description="The hypothesis text")
    confidence: float = Field(ge=0.0, le=1.0, description="Server-computed confidence score")
    confirmations: int = Field(ge=0, default=0, description="Number of confirmations from user replies")
    status: Literal["active", "confirmed", "discarded"] = Field(default="active")
    discard_reason: Optional[str] = Field(default=None, description="Why this hypothesis was discarded")


class Probe(BaseModel):
    """
    A contrastive Socratic question designed to discriminate between hypotheses.
    """
    probe_id: UUID = Field(default_factory=uuid4)
    question: str = Field(min_length=1, description="The contrastive question")
    targets: List[UUID] = Field(min_items=1, description="List of hypothesis_ids this probe targets")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProbeTurn(BaseModel):
    """
    Record of a probe-reply interaction and its analysis.
    """
    probe: Probe
    user_reply: str = Field(min_length=1, description="User's response to the probe")
    analysis: Optional[str] = Field(default=None, description="Short rationale of the belief update")
    signals: Optional[Dict[str, float]] = Field(default=None, description="Feature scalars used by scorer")
    updated_hypotheses: Optional[List[CruxHypothesis]] = Field(default=None, description="Snapshot after update")


class DiscardedHypothesisLogItem(BaseModel):
    """
    Record of rejected hypotheses for transparency and potential future use.
    """
    hypothesis_id: UUID
    text: str
    reason: str


class ExcavationState(BaseModel):
    """
    Server-canonical state for the interactive excavation process.
    """
    state_id: UUID = Field(default_factory=uuid4)
    revision: int = Field(ge=0, default=0, description="Monotonic server counter")
    integrity: Optional[str] = Field(default=None, description="Optional HMAC for tamper detection")
    
    journal_entry: JournalEntry
    hypotheses: List[CruxHypothesis] = Field(default_factory=list, max_items=4)
    probes_log: List[ProbeTurn] = Field(default_factory=list)
    last_probe: Optional[Probe] = Field(default=None)
    
    budget_used: int = Field(ge=0, default=0)
    exit_flags: Dict[str, bool] = Field(default_factory=dict, description="Exit condition diagnostics")


class ConfirmedCrux(BaseModel):
    """
    The validated root issue from the excavation process.
    """
    hypothesis_id: UUID
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class SecondaryTheme(BaseModel):
    """
    Additional themes that received some confirmation but weren't the main crux.
    """
    hypothesis_id: UUID
    text: str
    confirmations: int = Field(ge=1, description="Must have at least 1 confirmation")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ExcavationSummary(BaseModel):
    """
    Summary of the excavation process for transparency.
    """
    exit_reason: Literal["threshold", "confirmations", "budget"]
    reasoning_trail: str = Field(min_length=1, description="Narrative of validation & rival handling")
    discarded_log: List[DiscardedHypothesisLogItem] = Field(default_factory=list)


class ExcavationResult(BaseModel):
    """
    Final result of a completed excavation.
    """
    confirmed_crux: ConfirmedCrux
    secondary_themes: List[SecondaryTheme] = Field(default_factory=list)
    excavation_summary: ExcavationSummary


# ---- v2 API Request/Response Models -----------------------------------------

class ExcavationInitRequest(BaseModel):
    """
    Request to initialize a new excavation.
    """
    mode: Literal["init"]
    journal_entry: JournalEntry


class ExcavationStepRequest(BaseModel):
    """
    Request to continue an existing excavation.
    """
    mode: Literal["continue"]
    state: ExcavationState
    user_reply: str = Field(min_length=1)
    expected_probe_id: UUID = Field(description="Must match last server-issued probe")


class ExcavationStepResponse(BaseModel):
    """
    Response from an excavation step (init or continue).
    """
    complete: bool
    state: ExcavationState
    next_probe: Optional[Probe] = Field(default=None)
    exit_reason: Optional[Literal["threshold", "confirmations", "budget"]] = Field(default=None)
    result: Optional[ExcavationResult] = Field(default=None)


class ReflectionRequestV2(BaseModel):
    """
    Request to generate a reflection from a completed excavation.
    """
    from_excavation: ExcavationResult
    enable_scout: bool = Field(default=False)
    journal_entry: Optional[JournalEntry] = Field(
        default=None, 
        description="Optional if recoverable from excavation context"
    )


# ---- v3 FACD Models ---------------------------------------------------------

class CruxNode(BaseModel):
    """
    A hypothesis representing a candidate "crux" with supporting and counter signals.
    """
    node_id: UUID = Field(default_factory=uuid4)
    text: constr(min_length=1, max_length=400)
    priors: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="for diagnostics (0..1)")
    supports: List[str] = Field(default_factory=list, description="short rationales/snippets")
    counters: List[str] = Field(default_factory=list, description="counter-evidence snippets")
    status: Literal["active", "merged", "retired"] = Field(default="active")


class BeliefState(BaseModel):
    """
    Probability distribution over candidate CruxNodes.
    """
    nodes: List[CruxNode] = Field(default_factory=list, max_items=6)
    probs: Dict[UUID, float] = Field(default_factory=dict, description="normalized probabilities")
    top_ids: List[UUID] = Field(default_factory=list, description="cached ranking")


class Evidence(BaseModel):
    """
    Observations used to update beliefs.
    """
    kind: Literal["UserAnswer", "EntryQuote", "PatternSignal", "ContextDatum", "MicroExperimentResult"]
    payload: Dict[str, Any]
    at_revision: int


# ---- Actions (discriminated union) ---

class AskUserAction(BaseModel):
    """
    Action to ask the user a targeted question.
    """
    type: Literal["AskUser"] = "AskUser"
    action_id: UUID = Field(default_factory=uuid4)
    question: constr(min_length=1, max_length=200)
    quick_options: Optional[List[str]] = Field(default=None, description="2..4 options")
    targets: List[UUID] = Field(default_factory=list, description="nodes contrasted")
    rationale: Optional[str] = Field(default=None, description="one‑liner for UI")


class HypothesizeAction(BaseModel):
    """
    Action to generate new hypothesis nodes.
    """
    type: Literal["Hypothesize"] = "Hypothesize"
    action_id: UUID = Field(default_factory=uuid4)
    spawn_k: conint(ge=1, le=3) = 1


class ClusterThemesAction(BaseModel):
    """
    Action to cluster similar themes.
    """
    type: Literal["ClusterThemes"] = "ClusterThemes"
    action_id: UUID = Field(default_factory=uuid4)
    method: Literal["HDBSCAN", "spectral"] = "HDBSCAN"


class CounterfactualTestAction(BaseModel):
    """
    Action to test hypotheses with counterfactual scenarios.
    """
    type: Literal["CounterfactualTest"] = "CounterfactualTest"
    action_id: UUID = Field(default_factory=uuid4)
    test_spec: Dict[str, Any]


class EvidenceRequestAction(BaseModel):
    """
    Action to request specific evidence types.
    """
    type: Literal["EvidenceRequest"] = "EvidenceRequest"
    action_id: UUID = Field(default_factory=uuid4)
    kind: Literal["timeline", "constraints", "goals", "norms"]


class SilenceCheckAction(BaseModel):
    """
    Action to check for what's not being said.
    """
    type: Literal["SilenceCheck"] = "SilenceCheck"
    action_id: UUID = Field(default_factory=uuid4)


class ConfidenceUpdateAction(BaseModel):
    """
    Action to update confidence scores.
    """
    type: Literal["ConfidenceUpdate"] = "ConfidenceUpdate"
    action_id: UUID = Field(default_factory=uuid4)


class StopAction(BaseModel):
    """
    Action to stop the excavation process.
    """
    type: Literal["Stop"] = "Stop"
    action_id: UUID = Field(default_factory=uuid4)
    exit_reason: Literal["threshold", "epsilon", "budget", "guardrail"]


Action = Annotated[
    Union[AskUserAction, HypothesizeAction, ClusterThemesAction,
          CounterfactualTestAction, EvidenceRequestAction, SilenceCheckAction,
          ConfidenceUpdateAction, StopAction],
    Field(discriminator="type")
]


# ---- Agent state & I/O ---

class AgentState(BaseModel):
    """
    Complete state for the v3 agentic loop (round-tripped by client).
    """
    state_id: UUID = Field(default_factory=uuid4)
    revision: int = Field(default=0, ge=0, description="Monotonic server counter")
    integrity: Optional[str] = Field(default=None, description="optional HMAC")
    journal_entry: JournalEntry
    belief_state: BeliefState
    evidence_log: List[Evidence] = Field(default_factory=list)
    last_action: Optional[Action] = Field(default=None)
    budget_used: int = Field(default=0, ge=0)
    exit_flags: Dict[str, bool] = Field(default_factory=dict)


class ConfirmedCruxV3(BaseModel):
    """
    The confirmed crux from v3 FACD process.
    """
    node_id: UUID
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class SecondaryThemeV3(BaseModel):
    """
    Secondary themes from v3 FACD process.
    """
    node_id: UUID
    text: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AgentResult(BaseModel):
    """
    Final result from v3 FACD process.
    """
    confirmed_crux: ConfirmedCruxV3
    secondary_themes: List[SecondaryThemeV3] = Field(default_factory=list)
    reasoning_trail: str
    exit_reason: Literal["threshold", "epsilon", "budget", "guardrail"]


# ---- v3 API Request/Response Models ---

class AgentActInitRequest(BaseModel):
    """
    Request to initialize a new v3 agentic session.
    """
    mode: Literal["init"]
    journal_entry: JournalEntry


class AgentActStepRequest(BaseModel):
    """
    Request to continue an existing v3 agentic session.
    """
    mode: Literal["continue"]
    state: AgentState
    user_event: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="e.g., {'answer_to': action_id, 'value': '...'}"
    )


class AgentActResponse(BaseModel):
    """
    Response from v3 agentic action.
    """
    complete: bool
    state: AgentState
    action: Optional[Action] = Field(default=None)
    result: Optional[AgentResult] = Field(default=None)