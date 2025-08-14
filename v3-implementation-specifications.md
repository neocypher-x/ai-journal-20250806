# v3 Implementation Specifications — Fully‑Agentic Crux Discovery (FACD)

**Status:** Draft (v3)  
**Audience:** Backend/API engineers, agent authors, client engineers (web/iOS), QA.  
**Scope:** This document specifies **only** the changes and new components introduced in **v3**, relative to v2. It assumes familiarity with the v2 spec.  

---

## 0. Design Goals & Non‑Goals

### Goals
- Add a new **server‑agentic** loop that selects its own next action, including asking the user targeted questions.
- Optimize **information gain per unit user effort** using an EVI − λ·Cost policy to converge quickly on a confirmed crux and secondary themes.
- Preserve backwards compatibility for `/reflections` and `/v2/reflections` responses.
- Keep server **stateless** with canonical state round‑tripped by the client.

### Non‑Goals
- Persisting sessions in a DB or introducing long‑lived server state.
- Exposing internal scoring parameters or templates over the public API.
- Changing the surface schema of Reflection responses.

---

## 1. Versioning & Endpoints

| Endpoint              | Method | Purpose                                                                              | Status        |
| --------------------- | ------ | ------------------------------------------------------------------------------------ | ------------- |
| `/reflections`        | POST   | One‑shot from journal entry → Reflection (MVP behavior)                              | Unchanged     |
| `/v2/reflections`     | POST   | Generate Reflection from a completed excavation                                      | Unchanged     |
| `/v3/agent/act`       | POST   | **New** server‑agentic action loop (FACD). Returns next action or final result.      | **New**       |
| `/excavations`        | POST   | v2 interactive excavation                                                            | Unchanged |

**Notes**
- Server remains stateless; client must round‑trip the **AgentState** returned by `/v3/agent/act` each turn.

---

## 2. Interaction Model — Agentic Loop

The **server** now selects among a set of **Actions** each turn based on the current belief state. One of these actions is `AskUser`, which yields a user‑visible question similar to v2’s “probe”, but the action set is broader.

### 2.1 Turn Semantics
1. **Init (optional)**: Client sends `mode="init"` with a journal entry; server seeds beliefs and returns either an immediate `AskUser` action or proceeds internally.
2. **Step**: Client calls with `mode="continue"` carrying the prior `state` and optional `user_event` payload (answer to a prior `AskUser`).  
3. **Server** updates beliefs, **enumerates** candidate actions, **scores** them by expected info gain minus cost, **executes** the top action, and returns:
   - `complete=false` + `action` (e.g., `AskUser`, `CounterfactualTest`, …), **or**
   - `complete=true` + `result` (Confirmed Crux + Secondary Themes + Summary).

### 2.2 Exit Conditions
Stop when any is true:
- Confidence: `max p(h_i) ≥ τ_high` **and** `gap(top, second) ≥ δ_gap`  
- Diminishing returns: `best_action_EVI < ε`  
- Budget: `user_query_budget` or `step_budget` exhausted

---

## 3. Data Contracts (Pydantic Models)

> Only new or changed models are shown. Unchanged MVP/v2 models (e.g., `Reflection`, `JournalEntry`) are reused as‑is.

```python
# --- Core belief graph ---
class CruxNode(BaseModel):
    node_id: UUID = Field(default_factory=uuid4)
    text: constr(min_length=1, max_length=400)
    priors: Optional[float] = None                    # for diagnostics (0..1)
    supports: List[str] = []                          # short rationales/snippets
    counters: List[str] = []
    status: Literal["active","merged","retired"] = "active"

class BeliefState(BaseModel):
    nodes: List[CruxNode] = Field(default_factory=list, max_items=6)
    probs: Dict[UUID, float] = Field(default_factory=dict)    # normalized
    top_ids: List[UUID] = []                                  # cached ranking

# --- Evidence ---
class Evidence(BaseModel):
    kind: Literal["UserAnswer","EntryQuote","PatternSignal","ContextDatum","MicroExperimentResult"]
    payload: Dict[str, Any]
    at_revision: int

# --- Actions (discriminated union) ---
class AskUserAction(BaseModel):
    type: Literal["AskUser"] = "AskUser"
    action_id: UUID = Field(default_factory=uuid4)
    question: constr(min_length=1, max_length=200)
    quick_options: Optional[List[str]] = None                  # 2..4 options
    targets: List[UUID] = []                                   # nodes contrasted
    rationale: Optional[str] = None                            # one‑liner for UI

class HypothesizeAction(BaseModel):
    type: Literal["Hypothesize"] = "Hypothesize"
    action_id: UUID = Field(default_factory=uuid4)
    spawn_k: conint(ge=1, le=3) = 1

class ClusterThemesAction(BaseModel):
    type: Literal["ClusterThemes"] = "ClusterThemes"
    action_id: UUID = Field(default_factory=uuid4)
    method: Literal["HDBSCAN","spectral"] = "HDBSCAN"

class CounterfactualTestAction(BaseModel):
    type: Literal["CounterfactualTest"] = "CounterfactualTest"
    action_id: UUID = Field(default_factory=uuid4)
    test_spec: Dict[str, Any]

class EvidenceRequestAction(BaseModel):
    type: Literal["EvidenceRequest"] = "EvidenceRequest"
    action_id: UUID = Field(default_factory=uuid4)
    kind: Literal["timeline","constraints","goals","norms"]

class SilenceCheckAction(BaseModel):
    type: Literal["SilenceCheck"] = "SilenceCheck"
    action_id: UUID = Field(default_factory=uuid4)

class ConfidenceUpdateAction(BaseModel):
    type: Literal["ConfidenceUpdate"] = "ConfidenceUpdate"
    action_id: UUID = Field(default_factory=uuid4)

class StopAction(BaseModel):
    type: Literal["Stop"] = "Stop"
    action_id: UUID = Field(default_factory=uuid4)
    exit_reason: Literal["threshold","epsilon","budget","guardrail"]

Action = Annotated[
    Union[AskUserAction, HypothesizeAction, ClusterThemesAction,
          CounterfactualTestAction, EvidenceRequestAction, SilenceCheckAction,
          ConfidenceUpdateAction, StopAction],
    Field(discriminator="type")
]

# --- Agent state & I/O ---
class AgentState(BaseModel):
    state_id: UUID = Field(default_factory=uuid4)
    revision: int = 0
    integrity: Optional[str] = None        # optional HMAC
    journal_entry: JournalEntry
    belief_state: BeliefState
    evidence_log: List[Evidence] = []
    last_action: Optional[Action] = None
    budget_used: int = 0
    exit_flags: Dict[str, bool] = {}

class ConfirmedCrux(BaseModel):
    node_id: UUID
    text: str
    confidence: float

class SecondaryTheme(BaseModel):
    node_id: UUID
    text: str
    confidence: Optional[float] = None

class AgentResult(BaseModel):
    confirmed_crux: ConfirmedCrux
    secondary_themes: List[SecondaryTheme] = []
    reasoning_trail: str
    exit_reason: Literal["threshold","epsilon","budget","guardrail"]

class AgentActInitRequest(BaseModel):
    mode: Literal["init"]
    journal_entry: JournalEntry

class AgentActStepRequest(BaseModel):
    mode: Literal["continue"]
    state: AgentState
    user_event: Optional[Dict[str, Any]] = None  # e.g., {"answer_to": action_id, "value": "..."}

class AgentActResponse(BaseModel):
    complete: bool
    state: AgentState
    action: Optional[Action] = None
    result: Optional[AgentResult] = None
```

---

## 4. Endpoint Specifications

### 4.1 `POST /v3/agent/act`

**Statelessness**: Server does not persist `AgentState`; clients MUST round‑trip the latest `state` on `mode="continue"` calls. Any belief or scoring fields sent by clients are treated as advisory and are recomputed by the server each turn.

**Requests**
- **Init**
  ```json
  { "mode": "init", "journal_entry": { "text": "..." } }
  ```
- **Continue**
  ```json
  { "mode": "continue", "state": { "...": "server-issued state" }, "user_event": { "answer_to": "uuid", "value": "..." } }
  ```

**Responses**
- **In-progress**
  ```json
  { "complete": false, "state": { "revision": 1, ... }, "action": { "type": "AskUser", "question": "..." } }
  ```
- **Complete**
  ```json
  { "complete": true, "result": { "confirmed_crux": { "text": "...", "confidence": 0.86 }, "secondary_themes": [ ... ], "reasoning_trail": "...", "exit_reason": "threshold" }, "state": { "revision": 3, ... } }
  ```

**Validation & Errors**
- `409 Conflict` — stale `state.revision` or integrity mismatch
- `410 Gone` — `user_event.answer_to` does not match `state.last_action.action_id` when last action was `AskUser`
- `429 Too Many Requests` — budget or rate guard
- Standard `400/422/5xx` envelopes with stable `error_code`

**Idempotency**
- Support `Idempotency-Key` on `continue` calls (keyed by `state_id` + `revision`).

---

## 5. Algorithms (Normative Pseudocode)

### 5.1 `seed_beliefs(journal_entry) -> BeliefState`
- Extract 2–4 candidate crux themes from salience cues; initialize `probs` near‑uniform with mild priors.

### 5.2 `enumerate_actions(state) -> List[Action]`
- Always include at least one `AskUser` candidate (unless user budget exhausted).  
- Include `Hypothesize` when entropy is high and coverage is low.  
- Add `ClusterThemes` when semantic redundancy is detected.  
- Include `CounterfactualTest` to differentiate persistent vs. situational drivers.

### 5.3 `score_actions(actions, state) -> List[(Action, score)]`
- Use **expected entropy reduction** (Monte‑Carlo or discrete answer priors) minus `λ·Cost(action)`; set `Cost(AskUser) > Cost(internal)`.
- Calibrate λ and ε via offline grid search on synthetic/curated transcripts.

### 5.4 `execute(action, state) -> (obs|None)`
- For `AskUser`, return the question and pause for client reply (no observation yet).  
- For internal actions, produce an observation (`Evidence`) immediately and proceed to update.

### 5.5 `update_beliefs(state, obs) -> BeliefState`
- Featureize observation vs. each node (entail/contradict, specificity, novelty).  
- Update in log‑odds space with bounded step size and renormalize.  
- Merge near‑duplicate nodes (cosine ≥ MERGE_RADIUS).  
- Retire dominated nodes (low probability for K turns).

### 5.6 `should_stop(state) -> Optional[exit_reason]`
- Threshold: `max p(h) ≥ τ_high` & gap ≥ δ_gap  
- Epsilon: `best_action_EVI < ε`  
- Budget: queries or steps ≥ configured limits

### 5.7 `finalize(state) -> AgentResult`
- Select top node as `confirmed_crux`; include remaining high‑mass nodes as `secondary_themes`.  
- Emit a compact `reasoning_trail` from evidence log.

---

## 6. Parameters & Config

- `TAU_HIGH=0.80`, `DELTA_GAP=0.25`, `EPSILON_EVI=0.05`  
- `LAMBDA_COST`: 0.5–1.5 (tune by target interaction length)  
- Budgets: `MAX_USER_QUERIES=3`, `MAX_STEPS=8`  
- Belief graph: `MAX_HYPOTHESES=6`, `MERGE_RADIUS=0.92` (cosine)  
- Feature flags: `enable_scout_templates`, `enable_cluster_spectral`

---

## 7. State Integrity, Idempotency, Concurrency

- **Integrity**: Optional `state.integrity = HMAC(state_without_integrity, server_secret)`; verify on `continue` else `409`.  
- **Revision**: Increment once per successful turn; reject stale with `409`.  
- **Idempotency**: Same `Idempotency-Key` + (`state_id`,`revision`) returns the same result body for 2 minutes.  
- **Concurrency**: Accept the first `continue` for a given `revision`; subsequent parallel calls → `409`.

---

## 8. Observability

- **Metrics**: `agent_turns_total`, `agent_completions_total{exit_reason}`, `avg_action_latency_ms`, `askuser_rate`, `entropy_reduction_bits`.  
- **Tracing**: Span per turn; attrs: `state_id`, `revision`, `action.type`, `evi_bits`, `exit_reason`.  
- **Logs**: Hashes of prompts/questions, targets, top‑2 probabilities, merge events.

---

## 9. Safety & Guardrails

- **Distress gate** → `Stop(guardrail)`; return crisis resources (client renders).  
- **Bias checks** on leading question patterns (linter over `AskUser` wording).  
- **Privacy**: Stateless by default; client opts into history storage if needed.

---

## 10. Backward Compatibility & Coexistence

- `/reflections` & `/v2/reflections` unchanged.
- `/excavations` **unchanged** and supported; no clients have been built against it to date.
- v3 is **additive**. Teams can integrate directly with `/v3/agent/act`.
- Optional: an adapter may be used to reuse any v2-style UI flows by mapping a v2 `Probe` to a v3 `AskUserAction`, but this is not required.

## 11. OpenAPI 3.1 (Excerpt)

```yaml
openapi: 3.1.0
info:
  title: Agentic AI Journal API
  version: "3.0.0"
paths:
  /v3/agent/act:
    post:
      operationId: postAgentAct
      requestBody:
        required: true
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/AgentActInitRequest'
                - $ref: '#/components/schemas/AgentActStepRequest'
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentActResponse'
components:
  schemas:
    AgentActInitRequest: {}
    AgentActStepRequest: {}
    AgentActResponse: {}
    # (See §3 for Pydantic models; JSON Schemas mirror those shapes.)
```

---

## 12. Testing Notes (v3)

- **Golden path**: init → internal step → AskUser → continue → threshold exit; validate `exit_reason="threshold"` and entropy drop across turns.  
- **Epsilon exit**: use low‑entropy entry; ensure early stop by `EPSILON_EVI`.  
- **Budget exit**: set `MAX_USER_QUERIES=1`; expect `exit_reason="budget"`.  
- **Idempotency**: replay identical `continue` with same key → byte‑identical body.  
- **Integrity**: HMAC mismatch → `409 Conflict`.  
- **Migration**: feed a v2 state through adapter; ensure `AskUserAction` parity with prior `Probe`.

---

## 13. Implementation Hints

- Keep scoring deterministic per‑turn by fixing PRNG seeds for action sampling and answer priors; record the seed in logs.  
- Question bank: maintain contrastive templates indexed by hypothesis archetype; avoid repetition via hash‑based cooldown.  
- Belief updates in **log‑odds** with clipping to avoid saturation; decay stale nodes.
- Prefer tight 2‑way contrasts over multi‑way questions for higher EVI.