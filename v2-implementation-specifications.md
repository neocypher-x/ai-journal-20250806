# v2 Implementation Specifications

**Status:** Final (v2)

**Audience:** Backend/API engineers, agent authors, client engineers (web/iOS), QA.

**Summary:** v2 introduces an **interactive excavation** workflow as a new endpoint (`POST /excavations`) and a **generation-only** endpoint (`POST /v2/reflections`) that consumes a completed excavation. The original MVP endpoint `POST /reflections` remains **unchanged** for one-shot generation.

---

## 0. Design Goals & Non‑Goals

### Goals

- Support a **client-driven, stateless** back‑and‑forth excavation loop culminating in a validated crux and secondary themes.
- Keep `/reflections` (MVP) intact for simple one-shot flows.
- Make `/v2/reflections` consume a completed excavation result to produce the final **Reflection** (Perspectives + Prophecy) with the same surface contract as MVP.
- Ensure robustness via **server-canonical state**, integrity signaling, and idempotency without server persistence.

### Non‑Goals

- No server-side session storage or DB persistence.
- No exposure of internal thresholds or budgets. **Do not pass τ/δ/N/K between client and server.**

---

## 1. Versioning & Endpoints

| Endpoint          | Method | Purpose                                                 | Status      |         |
| ----------------- | ------ | ------------------------------------------------------- | ----------- | ------- |
| `/reflections`    | POST   | One-shot from journal entry → Reflection (MVP behavior) | Unchanged   |         |
| `/excavations`    | POST   | Interactive excavation loop (\`mode: init               | continue\`) | **New** |
| `/v2/reflections` | POST   | Generate Reflection from a **completed** excavation     | **New**     |         |

- **Stateless Server:** The server holds no session state; the **client must round‑trip** the canonical `ExcavationState` returned by the server each turn.
- **Server Constants:** τ\_high (confidence threshold), δ\_gap (margin to second-best), N\_confirmations (vote/turn count), K\_budget (max probe turns). These are **server‑only** constants, never sent by the client.

---

## 2. Interaction Model

### 2.1 `/excavations` — Interactive Loop

The loop alternates: **Server proposes a probe → Client answers**. On each turn the server recomputes beliefs, updates the canonical state, and either returns **next\_probe** or **complete=true** with a final `ExcavationResult`.

**Exit conditions (hybrid cascade, server enforced):**

1. `confidence(top) ≥ τ_high` **and** `confidence(top) – confidence(next) ≥ δ_gap`, or
2. `confirmations(top) ≥ N_confirmations`, or
3. `budget_used ≥ K_budget`.

**Statelessness contract:**

- Client sends back **the entire** server-issued `state` on each `continue` call.
- Server treats incoming belief fields as **advisory** only; it recomputes and **overwrites** them in the returned state.
- Optional integrity: `state.integrity` may carry an HMAC to detect tampering.

### 2.2 `/v2/reflections` — Generation Only

Consumes a **completed** `ExcavationResult` (confirmed crux + secondary themes + summary) and returns a `Reflection` identical in surface to the MVP response.

### 2.3 `/reflections` — MVP One‑Shot (Unchanged)

Runs excavation + generation in a single call, per MVP. Kept for convenience and backward compatibility.

---

## 3. Data Contracts (Pydantic Model Reference)

> Field constraints are normative; client generators should adhere to them. Enums are stable names.

### 3.1 MVP Models (Reused)

```python
class Framework(StrEnum):
    BUDDHISM = auto()
    STOICISM = auto()
    EXISTENTIALISM = auto()
    NEOADLERIANISM = auto()
    OTHER = auto()  # for Scout/user-defined

class AgreementStance(StrEnum):
    AGREE = auto()
    DIVERGE = auto()
    NUANCED = auto()

class JournalEntry(BaseModel):
    text: str  # min_length=1 (typical 300–1000 words)

class Perspective(BaseModel):
    framework: Framework
    other_framework_name: Optional[str]  # required iff framework=OTHER
    core_principle_invoked: str
    challenge_framing: str
    practical_experiment: str
    potential_trap: str
    key_metaphor: str

class Perspectives(BaseModel):
    items: List[Perspective]

class AgreementItem(BaseModel):
    framework_a: Framework
    framework_b: Framework
    stance: AgreementStance
    notes: Optional[str]

class TensionPoint(BaseModel):
    frameworks: List[Framework]  # len>=2
    explanation: str

class Prophecy(BaseModel):
    agreement_scorecard: List[AgreementItem]
    tension_summary: List[TensionPoint]
    synthesis: str
    what_is_lost_by_blending: List[str] = []

class Reflection(BaseModel):
    journal_entry: JournalEntry
    perspectives: Perspectives
    prophecy: Prophecy

class ReflectionRequest(BaseModel):
    journal_entry: JournalEntry
    enable_scout: bool = False

class ReflectionResponse(BaseModel):
    reflection: Reflection
```

### 3.2 v2 Excavation Models

```python
class CruxHypothesis(BaseModel):
    hypothesis_id: UUID = Field(default_factory=uuid4)
    text: str  # 1..400 chars
    confidence: float  # 0.0..1.0 (server-computed)
    confirmations: int = 0  # server-computed
    status: Literal["active","confirmed","discarded"] = "active"
    discard_reason: Optional[str] = None

class Probe(BaseModel):
    probe_id: UUID = Field(default_factory=uuid4)
    question: str  # contrastive Socratic question
    targets: List[UUID]  # ≥1 hypothesis_id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProbeTurn(BaseModel):
    probe: Probe
    user_reply: str
    analysis: Optional[str]  # short rationale of the update
    signals: Optional[Dict[str, float]]  # feature scalars used by scorer
    updated_hypotheses: Optional[List[CruxHypothesis]]  # snapshot *after* update

class DiscardedHypothesisLogItem(BaseModel):
    hypothesis_id: UUID
    text: str
    reason: str

class ExcavationState(BaseModel):
    state_id: UUID = Field(default_factory=uuid4)
    revision: int = 0  # monotonic server counter
    integrity: Optional[str]  # optional HMAC

    journal_entry: JournalEntry
    hypotheses: List[CruxHypothesis] = Field(default_factory=list, max_items=4)
    probes_log: List[ProbeTurn] = Field(default_factory=list)
    last_probe: Optional[Probe] = None

    budget_used: int = 0
    exit_flags: Dict[str, bool] = Field(default_factory=dict)  # diagnostics

class ConfirmedCrux(BaseModel):
    hypothesis_id: UUID
    text: str
    confidence: float  # 0.0..1.0

class SecondaryTheme(BaseModel):
    hypothesis_id: UUID
    text: str
    confirmations: int  # ≥1
    confidence: Optional[float] = None

class ExcavationSummary(BaseModel):
    exit_reason: Literal["threshold","confirmations","budget"]
    reasoning_trail: str  # narrative of validation & rival handling
    discarded_log: List[DiscardedHypothesisLogItem] = []

class ExcavationResult(BaseModel):
    confirmed_crux: ConfirmedCrux
    secondary_themes: List[SecondaryTheme] = []
    excavation_summary: ExcavationSummary

class ExcavationInitRequest(BaseModel):
    mode: Literal["init"]
    journal_entry: JournalEntry

class ExcavationStepRequest(BaseModel):
    mode: Literal["continue"]
    state: ExcavationState
    user_reply: str
    expected_probe_id: UUID  # must match last server-issued probe

class ExcavationStepResponse(BaseModel):
    complete: bool
    state: ExcavationState
    next_probe: Optional[Probe] = None
    exit_reason: Optional[Literal["threshold","confirmations","budget"]] = None
    result: Optional[ExcavationResult] = None

class ReflectionRequestV2(BaseModel):
    from_excavation: ExcavationResult  # must be complete
    enable_scout: bool = False
    journal_entry: Optional[JournalEntry] = None
```

---

## 4. Endpoint Specifications

### 4.1 POST `/excavations`

**Headers (recommended):**

- `Idempotency-Key` (string): for retry safety on `mode="continue"`.

**Requests:**

**Init**

```json
{
  "mode": "init",
  "journal_entry": { "text": "..." }
}
```

**Continue**

```json
{
  "mode": "continue",
  "state": { "...": "entire prior server state snapshot" },
  "user_reply": "free-text answer to last probe",
  "expected_probe_id": "uuid-from-previous-next_probe"
}
```

**Responses:**

**In-progress**

```json
{
  "complete": false,
  "next_probe": {
    "probe_id": "...",
    "question": "contrastive question",
    "targets": ["H1","H2"],
    "created_at": "2025-01-01T00:00:00Z"
  },
  "state": { "revision": 1, "journal_entry": {"text":"..."}, "hypotheses": [ ... ], "budget_used": 1 }
}
```

**Complete**

```json
{
  "complete": true,
  "exit_reason": "threshold",
  "result": {
    "confirmed_crux": { "hypothesis_id": "H1", "text": "...", "confidence": 0.86 },
    "secondary_themes": [{ "hypothesis_id": "H2", "text": "...", "confirmations": 1 }],
    "excavation_summary": {
      "exit_reason": "threshold",
      "reasoning_trail": "why H1 was confirmed and rivals handled",
      "discarded_log": [{ "hypothesis_id": "H3", "text": "...", "reason": "insufficient contrast" }]
    }
  },
  "state": { "revision": 3, "budget_used": 3 }
}
```

**Validation & Errors:**

- `400 Bad Request` — invalid `mode` or shape.
- `409 Conflict` — stale `state.revision` or integrity/HMAC mismatch.
- `410 Gone` — `expected_probe_id` does not match `state.last_probe.probe_id`.
- `422 Unprocessable Entity` — schema errors (missing fields, type issues).
- `429 Too Many Requests` — budget or rate guard before state update.
- `5xx` — internal errors (return a stable error envelope with `error_code`, `message`, `retryable`).

**Server Behavior:**

- Recompute `hypotheses[*].confidence`/`confirmations` from scratch each turn.
- Overwrite any client-provided belief fields.
- Increment `revision` and `budget_used` appropriately.
- Set `exit_flags` diagnostics (e.g., `{"passed_threshold": true, "budget_exhausted": false}`) in `state`.

### 4.2 POST `/v2/reflections`

**Request**

```json
{
  "from_excavation": { "...": "a completed ExcavationResult" },
  "enable_scout": false,
  "journal_entry": { "text": "..." }
}
```

`journal_entry` may be omitted if recoverable from the excavation context.

**Response**

```json
{ "reflection": { "journal_entry": { ... }, "perspectives": { "items": [ ... ] }, "prophecy": { ... } } }
```

**Validation & Errors:**

- `400` — input is not a completed result (e.g., `exit_reason` missing).
- `422` — schema problems.

**Behavior:**

- Deterministic generation-only pipeline that maps the confirmed crux + themes into Perspectives and Prophecy (per MVP structure). Respect `enable_scout` to optionally propose an additional `Framework.OTHER` perspective when useful.

### 4.3 POST `/reflections` (MVP — unchanged)

**Request**

```json
{ "journal_entry": { "text": "..." }, "enable_scout": false }
```

**Response** — same as `/v2/reflections` response schema.

---

## 5. Algorithms (Normative Pseudocode)

### 5.1 `seed_hypotheses(journal_entry) -> List[CruxHypothesis]`

- Extract 2–4 concise candidates from the entry using salience cues (goal/obstacle, affect intensity, recurrence terms).
- Initialize `confidence≈0.4±ε`, `confirmations=0`, `status="active"`.

### 5.2 `plan_next_probe(state) -> Probe`

- Choose a **contrastive** question that maximally distinguishes the current top‑2 hypotheses.
- `targets = [top1.hypothesis_id, top2.hypothesis_id]` when possible; fall back to single-target clarifier if only one remains.
- Ensure no duplicate probe wording; adapt based on `probes_log`.

### 5.3 `update_beliefs(state, user_reply) -> List[CruxHypothesis]`

- Score features: entailment/contradiction vs. each hypothesis, specificity, novelty, self‑report markers.
- Update: `confidence_i ← clip(sigmoid(w·f_i + bias))`.
- If reply strongly supports `Hk`, increment `Hk.confirmations`.
- If `confidence_i` falls below discard band for ≥2 turns, set `status="discarded"` and log reason.

### 5.4 `check_exit(hypotheses, budget_used) -> Optional[(exit_reason, result)]`

- If threshold rule satisfied → `exit_reason="threshold"`.
- Else if `max(confirmations) ≥ N_confirmations` → `exit_reason="confirmations"`.
- Else if `budget_used ≥ K_budget` → `exit_reason="budget"`.
- On exit: create `ConfirmedCrux` (top alive), `SecondaryTheme`s (others with confirmations≥1), and `ExcavationSummary` (reasoning trail + discarded rivals).

### 5.5 `validate_and_summarize(state) -> ExcavationResult`

- Build a terse, auditable trail from `probes_log` linking evidence → belief updates → decision.

---

## 6. State Integrity, Idempotency, and Concurrency

- **Integrity:**
  - Optional `state.integrity = HMAC(state.payload_without_integrity, server_secret)`.
  - On `continue`, verify HMAC; if fails, `409 Conflict`.
- **Revision:**
  - `state.revision` increments by 1 on every successful turn; reject stale revisions with `409 Conflict`.
- **Idempotency:**
  - If `Idempotency-Key` repeats within a 2‑minute window for the same `state.state_id` and `expected_probe_id`, return the **same** prior response.
- **Race safety:**
  - If two `continue` calls arrive for the same revision, accept only the first successful one; subsequent are `409`.

---

## 7. Security & Safety

None

---

## 8. Observability

- **Metrics:**
  - `excavation_turns_total`, `excavation_completions_total{exit_reason}`, `avg_probe_latency_ms`, `discard_rate`.
- **Tracing:**
  - Span per request; attributes: `state_id`, `revision`, `exit_reason`, `num_hypotheses`, `targets_count`.
- **Logs:**
  - On each turn: probe text hash, targets, signals summary, top2 confidences, decision rationale hash.

---

## 9. Backward Compatibility

- `/reflections` remains identical to MVP to avoid breaking existing clients.
- New clients should prefer `/excavations` + `/v2/reflections` to gain explainability and better crux validation.

---

## 10. OpenAPI 3.1 Excerpt (canonical shapes)

```yaml
openapi: 3.1.0
info:
  title: Agentic AI Journal API
  version: "2.0.0"
paths:
  /excavations:
    post:
      operationId: postExcavations
      requestBody:
        required: true
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/ExcavationInitRequest'
                - $ref: '#/components/schemas/ExcavationStepRequest'
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExcavationStepResponse'
  /v2/reflections:
    post:
      operationId: postReflectionsV2
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReflectionRequestV2'
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReflectionResponse'
  /reflections:
    post:
      operationId: postReflectionsV1
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReflectionRequest'
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReflectionResponse'
components:
  schemas:
    # (Include JSON Schema translations of the Pydantic models from §3.)
```

---

## 11. Error Envelope (Recommended)

```json
{
  "error_code": "STATE_INTEGRITY_MISMATCH",
  "message": "state.integrity does not match server-computed HMAC",
  "retryable": false,
  "details": { "state_id": "...", "expected_revision": 2 }
}
```

**Common codes:**

- `INVALID_MODE`, `INVALID_SHAPE`, `STALE_REVISION`, `STATE_INTEGRITY_MISMATCH`, `PROBE_ID_MISMATCH`, `BUDGET_EXHAUSTED`, `RATE_LIMITED`, `INTERNAL`.

---

## 12. Testing Notes

- **Golden flow:** init → 2–3 continue turns → threshold exit; confirm `revision` increments, `budget_used` counts, and `exit_reason="threshold"`.
- **Budget exit:** set `K_budget=1` in test config; ensure `exit_reason="budget"` when no threshold reached.
- **Mismatch handling:** send wrong `expected_probe_id` and expect `410 Gone`.
- **Tamper detection:** flip one byte in `state.hypotheses[0].confidence` and expect `409 Conflict` when HMAC enabled.
- **Idempotency:** replay the same `continue` with identical `Idempotency-Key` and expect byte-identical body.

---

## 13. Implementation Hints

- Keep τ/δ/N/K in config/env; expose to code as constants.
- Keep `hypotheses` ≤4 for tractability and better probes.
- Prefer contrastive probes over generic clarifiers; rotate question templates to avoid repetition.
- When producing `Reflection`, carry the **original** `journal_entry` to avoid drift.
