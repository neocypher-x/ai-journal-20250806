# AI Journal System – Specifications

## 1. Purpose

- **Primary outcome**: Confront and validate the root issue (**crux**) in a user journal entry, then generate a reflection focused on that crux.
- **Secondary outcome**: Weave **confirmed secondary themes** into the reflection.
- **Philosophical scope**: Core grounding in **Buddhism**, **Stoicism**, **Existentialism**, and **NeoAdlerianism**; optional **Scout** agent may propose an additional framework.

---

## 1.1 Core Entities

* **JournalEntry** — Raw text provided by the user.
* **CruxHypothesis** — Candidate statement representing a potential root issue.
* **Probe** — Contrastive Socratic question designed to discriminate between hypotheses.
* **ExcavationSummary** — Record of hypotheses, probes, confidence updates, exit reason, and reasoning trail.
* **PerspectiveAgent** — Produces a **Perspective** from the confirmed crux and secondary themes.
* **Buddhist**, **Stoic**, **Existentialist**, **NeoAdlerian** — Core **PerspectiveAgents** that each generate one *Perspective*.
* **Scout** *(optional)* — Agent that proposes an additional framework (philosophical or psychological) and generates its *Perspective*.
* **Perspective** — Output of one framework's reflection.
* **Perspectives** — Collection of all *Perspective* objects for a session.
* **Oracle** — Meta-analysis agent that produces the **Prophecy** from all *Perspectives*.
* **Prophecy** — Cross-framework synthesis.
* **Reflection** — Contains *Perspectives* and the *Prophecy*.
* **DiscardedHypothesisLogItem** — Record of rejected hypotheses for possible future use.

---

## 1.2 Primary Use Case (MVP Focus)

**Perspective** - One Perspective per framework (Buddhism, Stoicism, Existentialism, NeoAdlerianism, plus any from the optional Scout).

### A. Fully-Agentic Crux Discovery (FACD)

#### Purpose
“Fully-Agentic Crux Discovery (FACD)" is a fully agentic discovery process that selects its own next action—including querying the user—to efficiently converge on a small set of crux hypotheses that best explain the user’s current difficulty.

#### Overview
FACD operates as a planner–executor loop maintaining a belief state over dynamic crux hypotheses. At each step, the agent enumerates possible actions and chooses the one with the highest expected information gain net of user‑effort cost. It stops when confidence and separation thresholds are met or when marginal information gain falls below a minimum.

#### Core Concepts
- **BeliefState**: Probability distribution over candidate **CruxNodes**.
- **CruxNode**: A hypothesis representing a candidate “crux” with supporting and counter signals; nodes may be active, merged, or retired.
- **Evidence**: Observations used to update beliefs (user answers, salient entry quotes, pattern signals, contextual data, micro‑experiment results).
- **Action Set**: `AskUser`, `Hypothesize`, `ClusterThemes`, `CounterfactualTest`, `EvidenceRequest`, `SilenceCheck`, `ConfidenceUpdate`, `Stop`.

#### Control Policy (Information Gain with Cost)
Actions are selected by the expected reduction in uncertainty (entropy) less a user‑effort cost:
\[
\operatorname*{argmax}_a \; \mathbb{E}_{o \sim P(o \mid a)}\!\left[ H(p(H)) - H\!\big(p(H\mid o)\big) \right] - \lambda\,\mathrm{Cost}(a)
\]
- **Information term**: expected entropy reduction over crux hypotheses.
- **Cost term**: models effort/time; `AskUser` has higher cost than internal steps.
- **Termination**: stop when any holds: (i) confidence threshold \(\max_i p(h_i) \ge \tau\) **and** gap \(\ge \delta\); (ii) best‑action EVI < \(\varepsilon\); (iii) user‑query or step budget reached.

#### Parameters
- `TAU_HIGH` (\(\tau\)), `DELTA_GAP` (\(\delta\)) — confidence and separation thresholds.
- `EPSILON_EVI` (\(\varepsilon\)) — minimum expected info gain to continue.
- `LAMBDA_COST` (\(\lambda\)) — user‑effort trade‑off.
- `MAX_USER_QUERIES` — budget for `AskUser` actions.
- `MAX_HYPOTHESES`, `MERGE_RADIUS` — hypothesis graph maintenance.
**Recommended defaults (MVP):** `TAU_HIGH=0.80`, `DELTA_GAP=0.25`, `EPSILON_EVI=0.05`, `MAX_USER_QUERIES=3`.

#### UX Requirements
- Present one **Agent move** at a time; for `AskUser`, use ≤200‑char question with 2–4 quick options and “Other…”.  
- Display a compact **beliefs bar** (top‑3 with probabilities) and a one‑line “Why this question?” rationale.  
- Allow **Skip**; treat non‑response as evidence. Provide a **Stop** affordance with best‑current crux + uncertainty if invoked.

#### Telemetry & Evaluation
- Log per‑step: candidate actions, chosen action, EVI estimate, user‑effort cost, response latency.  
- Metrics: entropy reduced per user question, convergence stability, human face‑validity of cruxes, and downstream reflection quality lift.

#### Safety & Privacy
- Stateless MVP by default; offer opt‑in history later. Use neutral, non‑leading phrasing and avoid reinforcing harmful beliefs.

#### Integration
On completion, FACD returns a **confirmed crux** plus **secondary themes**; these are handed to existing Perspective/Oracle components without further changes.

### B. Perspective (per Framework)

Inside a Perspective, each framework produces:

| Output Element                         | Description                                                                                                                          | Example                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Core Principle Invoked**             | 1–2 sentence distillation of which central doctrine is relevant. Helps the user anchor advice to a framework, not just "AI opinion." | "This reflects impermanence."                                      |
| **Challenge Framing**                  | A short, provocative reframe to provoke thought.                                                                                     | "You are clinging to the illusion of control."                     |
| **Practical Micro-Experiment**         | One action to try within 24 hours that embodies the teaching. Keeps it behaviorally grounded.                                        | "Journal one thing you fear losing and reframe it as impermanent." |
| **Potential Trap / Misinterpretation** | Warning on how advice might be misused.                                                                                              | "Beware of treating non-attachment as avoidance."                  |
| **Key Metaphor or Image**              | A vivid, memorable one-line metaphor aligned to the tradition. This sticks better in memory.                                         | "Like a sailor adjusting sails to the wind…"                       |

*Note*: If the optional **Scout** agent is active, it generates an additional Perspective following this same structure (this may include other psychology frameworks such as **CBT**, **ACT**, or philosophical traditions like **Taoism**).

---

### C. Prophecy (Oracle)

Once all Perspective outputs are generated, the **Oracle** produces the **Prophecy**, which is the cross-framework meta-analysis. The Prophecy consists of:

1. **Agreement Scorecard**

   * For each pair of frameworks: Mark *Agree / Diverge / Nuanced*.

2. **Tension Summary**

   * Explain *why* they diverge, citing core principles.

3. **Synthesis**

   * Weave a unified principle or plan that respects all perspectives.

4. **What is Lost by Blending**

   * Explicit bullet points of philosophical/psychological richness forfeited by compromise.
     *Example*:

     * "Buddhist emphasis on impermanence is softened."
     * "Existential urgency is reduced in favor of Stoic steadiness."
     * "NeoAdlerian task separation loses its absolutist clarity."

---

### D. End‑to‑End Session Flow (Agentic, Stateless Across Sessions)

1. **Input**: User provides a *JournalEntry* (Markdown or plain text).
2. System runs **Fully-Agentic Crux Discovery (FACD)** to a **validated crux** (with explicit reasoning).
3. System generates **Perspectives** (all active frameworks) using *crux + secondary themes*.
4. **Oracle generates the Prophecy**: The **Oracle** reviews all *Perspectives* and produces the *Prophecy*.
5. System returns **Reflection** + **ExcavationSummary** (for transparency).
6. **Stateless constraint**: no cross‑session memory is consulted or injected into outputs (discarded hypotheses may be stored for future use but never auto‑injected).

---

## 2. User & Context

* **User base**: Single user (Chris)
* **Session frequency**: On-demand ad-hoc queries

## 3. Parameters (Default)

These parameters are defined on the server.

- τ_high = 0.80
- δ_gap = 0.25
- N_confirmations = 2
- K_budget = 4
- Max hypotheses = 4
- Socratic excavation style.

### 3.1 Journal Entry Requirements

* **Input formats**: Markdown (.md) or plain text (.txt)
* **Source**: Local file system (possible cloud integration later)
* **Ingestion cadence**: Real-time processing upon save or upload
* **Entry size**: 300–1000 words typical

## 4. Outputs
* **ReflectionResponse**: Contains Reflection + ExcavationSummary.
* **HiddenHypothesisLog**: Accessible only on explicit request.

## 5. Guarantees
* Every plausible hypothesis is confirmed, discarded with reason, or promoted to secondary theme before exit.
* Explicit reasoning presented at validation.
* Discarded hypotheses excluded from Prophecy by default.

## 6 Architecture Notes

What pattern is this?
- **ReAct (Reason+Act)** — During probing, the “act” step is a discriminative probe to test crux hypotheses. Control policy is explicit (τ/δ/N/K) rather than open-ended.
- **Reflexion / Self-critique** — Explicit reasoning at validation, down-ranking discarded paths; critique targets hypothesis selection.
- **Tree/Graph-of-Thoughts** — Small frontier of competing cruxes pruned via questions (shallow ToT specialized for diagnosis).
- **Plan-and-Execute** — Minimal planning (choose next probe), execution is asking; plan updates after evidence.
- **Active Inference / Experimental Design** — Selects maximally discriminative questions (information gain) until termination.
- **Orchestrated multi-agent system** — After crux confirmation, dispatches to PerspectiveAgents + Oracle.

Net: Architecture is a **Statechart-controlled, hypothesis-testing ReAct variant feeding specialist agents.**

### Reference Architecture
1. **Policy & Control (brain)**
    - Objective: confront root issue + weave secondary themes.
    - Constraints: τ_high, δ_gap, N_confirmations, K_budget; Socratic style; validation required.
    - Controller: explicit statechart (Seed → Probe → UpdateBeliefs → CheckExit → Validate → Generate → Deliver).
    - Termination: hybrid cascade.
2. **Deliberation Engine (hypothesis loop)**
    - Hypothesis Manager: ≤4 CruxHypothesis.
    - Probe Planner: chooses next contrastive question (info gain).
    - Evidence Scorer: updates confidences & confirmations; records reasoning trail.
    - Hidden Hypothesis Log: stores discarded items for future use.
3. **Specialist Layer (post-validation)**
    - PerspectiveAgents: generate perspectives.
    - Oracle: composes Prophecy focused on confirmed crux, weaving secondary themes.
4. **I/O & Platform**
    - Persistence: optional store for discarded hypotheses; session logs for tuning.

**Why Statechart?**
- Clear transitions, guard conditions (τ/δ/N/K), predictable recovery, debuggability.
- Prevents wandering (common ReAct failure).

**Comparisons**
- vs ReAct: Less tool-centric, more diagnostic.
- vs Tree/Graph-of-Thoughts: Shallow, contrastive search.
- vs Reflexion: Critique at validation improves correction.
- vs Debate: Avoids verbosity, still captures tensions.

**Implementation Notes**
- Question selection: Start with info gain.
- Confidence calibration: Conservative τ/δ.
- Determinism: Low temp for probes; slightly higher for Perspectives/Prophecy.
- Telemetry: Log exit_reason, scores per probe, validation outcome.
- Safety/UX: Budget exits should convey uncertainty.

Pattern Name: **Contrastive Socratic Agent (CSA) — statechart-controlled, hypothesis-testing ReAct variant with specialist synthesis.**

## 7. Personalization

TBD

## 8. Knowledge & Citations

* **Citation requirement**: Not required for MVP
* **Knowledge base**:

  * Philosophy & modern psychology (CBT/ACT, etc.)
  * No private library integration initially

## 9. Safety, Privacy & Data Handling

* **Storage**: Local storage only for MVP
* **Retention**: All data kept unless manually deleted
* **Security**: No encryption for MVP (possible in future)
* **Audit logs**: Conversation and processing logs stored locally

## 10. Capabilities & Tools

* **State**: Stateless (no persistent memory in MVP)
* **Tools**: None in MVP (future expansion possible)
* **Multimodal**: Text only for MVP
* **Offline mode**: Not required

## 11. System Design

* **Architecture**: Multi-agent system:

  * **PerspectiveAgent** (abstract base/interface)
  * **Core Agents**: **BuddhistAgent**, **StoicAgent**, **ExistentialistAgent**, **NeoAdlerianAgent** (implement PerspectiveAgent)
  * **Scout Agent** (optional) → proposes other **Framework** (e.g., **CBT**, **ACT**, **Taoism**) and generates a corresponding Perspective
  * **Oracle** → reviews all Perspectives and produces the Prophecy
* **Model baseline**: gpt-5-nano
* **Retrieval strategy**: None in MVP (no RAG)
* **Prompting strategy**: Iterative experimentation allowed
* **Additional technologies**: FastAPI
* **Error handling**: Minimal fallback behavior if ingestion or processing fails

## 12. UX & Product Surface

* **Interfaces**:

  * MVP: CLI or API endpoints
  * Later: Web app, possibly mobile
* **Session types**: One unified reflection session type for MVP
* **Notifications**: None in MVP
* **Accessibility**: None in MVP

## 13. Evaluation & Telemetry

* **Metrics**:

  * User-provided rubric scoring
  * Thumbs up/down feedback
* **Red-teaming**: Basic manual evaluation in MVP

## 14. Legal & Ethics

* **Licensing**: TBD for texts and quotations
* **Data processing agreements**: Not applicable in MVP

## 15. Delivery & Roadmap

TBD

## 16. Architecture (MVP — Stateless)

TBD