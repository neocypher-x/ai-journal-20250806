# Agentic AI Journal System – Specifications

## 1. Purpose

* **Primary outcome**: The system will provide a reflection response when given a user journal entry.
* **Philosophical scope**: Core grounding in **Buddhism**, **Stoicism**, and **Existentialism**. Optional **Scout** agent proposes relevant ideas from other frameworks when applicable.

---

## 1.1 Core Entities

* **JournalEntry** — Raw text provided by the user for reflection.
* **PerspectiveAgent** — Abstract base agent/interface that produces a **Perspective** from a **JournalEntry**. Implemented by concrete agents (e.g., **Buddhist**, **Stoic**, **Existentialist**) and any optional frameworks suggested by **Scout**.
* **Perspective** — Output of one framework’s reflection on the journal entry.
* **Perspectives** — Collection of all *Perspective* objects generated in a session (one per active framework).
* **Buddhist**, **Stoic**, **Existentialist** — Core **PerspectiveAgents** that each generate one *Perspective*.
* **Scout** *(optional)* — Agent that proposes an additional framework (philosophical or psychological) and generates its *Perspective*.
* **Oracle** — Meta-analysis agent that produces the **Prophecy** from all *Perspectives*.
* **Prophecy** — Cross-framework meta-analysis and synthesis output from the *Oracle*.
* **Reflection** — Top-level container for the system’s output; contains *Perspectives* and the *Prophecy*.

---

## 1.2 Primary Use Case (MVP Focus)

**Perspective** - One Perspective per framework (Buddhism, Stoicism, Existentialism, plus any from the optional Scout).

### A. **Perspective**

Inside a Perspective, each framework produces:

| Output Element                         | Description                                                                                                                          | Example                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Core Principle Invoked**             | 1–2 sentence distillation of which central doctrine is relevant. Helps the user anchor advice to a framework, not just “AI opinion.” | “This reflects impermanence.”                                      |
| **Challenge Framing**                  | A short, provocative reframe to provoke thought.                                                                                     | “You are clinging to the illusion of control.”                     |
| **Practical Micro-Experiment**         | One action to try within 24 hours that embodies the teaching. Keeps it behaviorally grounded.                                        | “Journal one thing you fear losing and reframe it as impermanent.” |
| **Potential Trap / Misinterpretation** | Warning on how advice might be misused.                                                                                              | “Beware of treating non-attachment as avoidance.”                  |
| **Key Metaphor or Image**              | A vivid, memorable one-line metaphor aligned to the tradition. This sticks better in memory.                                         | “Like a sailor adjusting sails to the wind…”                       |

*Note*: If the optional **Scout** agent is active, it generates an additional Perspective following this same structure (this may include psychology frameworks such as **Adlerian Psychology**).

---

### B. **Prophecy**

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

     * “Buddhist emphasis on impermanence is softened.”
     * “Existential urgency is reduced in favor of Stoic steadiness.”

---

### C. MVP-Friendly Flow (Stateless)

1. **Input**: User provides a *JournalEntry* (Markdown or plain text).
2. **PerspectiveAgents generate Perspectives**: Each active agent (Buddhist, Stoic, Existentialist, and optional **Scout**) produces its Perspective using the JournalEntry.
3. **Oracle generates the Prophecy**: The **Oracle** reviews all *Perspectives* and produces the *Prophecy*.
4. **Output**: A **Reflection** object containing:

   * **Perspectives** — individual outputs.
   * **Prophecy** — cross-perspective synthesis and analysis.
5. **Stateless Constraint**: Each *JournalEntry* is processed in isolation; there is no cross-session memory or recall in the MVP.

---

## 2. User & Context

* **User base**: Single user (Chris)
* **Session frequency**: On-demand ad-hoc queries

## 3. Journal Entry Requirements

* **Input formats**: Markdown (.md) or plain text (.txt)
* **Source**: Local file system (possible cloud integration later)
* **Ingestion cadence**: Real-time processing upon save or upload
* **Entry size**: 300–1000 words typical

## 4. Conversation & Behavior

* **Tone**: Can shift between Socratic questioning and direct guidance.
* **Depth levels**:

  * Surface-level observations
  * Text-cited analysis (when needed)
* **Boundaries**: No excluded topics for MVP.
* **Proactivity**: None in MVP (user-initiated).

## 5. Personalization

TBD

## 6. Knowledge & Citations

* **Citation requirement**: Not required for MVP
* **Knowledge base**:

  * Philosophy & modern psychology (CBT/ACT, etc.)
  * No private library integration initially

## 7. Safety, Privacy & Data Handling

* **Storage**: Local storage only for MVP
* **Retention**: All data kept unless manually deleted
* **Security**: No encryption for MVP (possible in future)
* **Audit logs**: Conversation and processing logs stored locally

## 8. Capabilities & Tools

* **State**: Stateless (no persistent memory in MVP)
* **Tools**: None in MVP (future expansion possible)
* **Multimodal**: Text only for MVP
* **Offline mode**: Not required

## 9. System Design

* **Architecture**: Multi-agent system:

  * **PerspectiveAgent** (abstract base/interface)
  * **Core Agents**: **BuddhistAgent**, **StoicAgent**, **ExistentialistAgent** (implement PerspectiveAgent)
  * **Scout Agent** (optional) → proposes other **Framework** (e.g., **Adlerian Psychology**, **ACT**, **Taoism**) and generates a corresponding Perspective
  * **Oracle** → reviews all Perspectives and produces the Prophecy
* **Model baseline**: gpt-5-nano
* **Retrieval strategy**: None in MVP (no RAG)
* **Prompting strategy**: Iterative experimentation allowed
* **Additional technologies**: FastAPI
* **Error handling**: Minimal fallback behavior if ingestion or processing fails

## 10. UX & Product Surface

* **Interfaces**:

  * MVP: CLI or API endpoints
  * Later: Web app, possibly mobile
* **Session types**: One unified reflection session type for MVP
* **Notifications**: None in MVP
* **Accessibility**: None in MVP

## 11. Evaluation & Telemetry

* **Metrics**:

  * User-provided rubric scoring
  * Thumbs up/down feedback
* **Red-teaming**: Basic manual evaluation in MVP

## 12. Legal & Ethics

* **Licensing**: TBD for texts and quotations
* **Data processing agreements**: Not applicable in MVP

## 13. Delivery & Roadmap

TBD

## 14. Architecture (MVP — Stateless)

TBD