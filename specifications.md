# Agentic AI Journal System Specification

## 1 Overview
An end-to-end personal AI assistant that ingests Chris’s markdown journal, reasons with philosophical frameworks (Buddhism, Stoicism, Existentialism, and related schools), and provides self-reflection prompts and advice via text chat (voice optional in future iterations).

## 2 Goals & Outcomes
* **Primary outcome** – actionable reflection prompts and philosophically grounded advice tailored to journal content.  
* **Secondary outcome** – persistent memory of user preferences and themes for continuity across sessions.

## 3 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | **Journal Ingestion** – ingest a single, growing markdown file (~300‑1 000 words per entry, near‑daily frequency). |
| FR-2 | **Philosophical Dialogue** – answer questions or initiate prompts drawing from Stoicism, Buddhism, Existentialism, or any related school. |
| FR-3 | **Persona Agents (MVP)** – selectable agents (Stoic Mentor, Buddhist Monk, Existentialist Philosopher). |
| FR-4 | **On‑Demand Interaction** – user triggers sessions; no scheduled check‑ins initially. |
| FR-5 | **Citation & Grounding** – optionally surface journal excerpts or canonical text passages to justify advice. |
| FR-6 | **External Corpus Access** – query indexed canonical texts provided by user (Stoic works, sutras, existentialist literature). |
| FR-7 | **Long‑Term Memory** – persist user traits, recurring dilemmas, and resolved / unresolved topics. |
| FR-8 | **Audit Logging** – store all model calls, retrieved excerpts, and agent outputs for debugging purposes. |
| FR-9 | **Inline Feedback** – chat UI shows 👍 / 👎 buttons plus optional free‑text field after every agent response; all feedback is logged with timestamp and conversation ID. |
| FR-10 | **Persona Selector UI** – provide a UI control (e.g., dropdown or side‑panel toggle) for switching among personas at any time during a session. |
| FR-11 | **Crisis Detection** – run a lightweight classifier on each user message; if potential self‑harm language is detected above a configurable threshold, the agent delivers a baseline supportive response and flags the exchange for later tuning. |

## 4 Architecture
1. **Ingestion Service** → parses markdown, timestamps entries, embeds → vector DB.  
2. **Corpus Indexer** → same pipeline for canonical philosophical texts.  
3. **Agent Framework**:  
   • **Persona Layer** – template + retrieval chain per philosophy.  
   • **Routing Layer** – selects persona or merges outputs.  
4. **Conversation API** – front‑end chat UI; websocket for future voice.  
5. **Memory Store** – key‑value DB for long‑term facts.  
6. **Logging & Analytics** – centralized store + dashboard.

## 5 Model & Tooling Choices (MVP)
* **LLM** – GPT‑4o via API (no fine‑tuning).  
* **Embeddings** – OpenAI `text-embedding-3-large`.  
* **Vector DB** – pgvector or Qdrant (managed).  
* **Agent Orchestration** – OpenAI Agents SDK / Agno / SmolAgents

## 6 Security & Privacy
* Data encrypted at rest and TLS in transit.  
* Access limited to single user account (Chris).  
* Future option: local‑only deployment with open‑source LLMs (e.g., Llama‑3).

## 7 Evaluation & Feedback

| Metric | Detail |
|--------|--------|
| **Rubric Score** | After each session, user selects a 1–5 “helpfulness” rating (skippable). |
| **Thumbs Feedback** | 👍 / 👎 buttons after every agent turn; optional free‑text explanation. |
| **Qualitative Notes** | Optional free‑text field attached to rubric score for context. |
| **Review Dashboard** | Weekly summary: score distribution, low‑scoring (< 3) turns, and all 👎 events with comments. |

## 8 Open Questions
All previously listed open questions (#1–#4) are now resolved; future questions will be tracked here.

## 9 Roadmap

| Phase | Timeline | Scope |
|-------|----------|-------|
| **P0** | Week 1 | Repo setup, choose vector DB, initial markdown ingestion. |
| **P1** | Weeks 2–3 | Retrieval‑augmented chat with single generic philosopher agent. |
| **P2** | Weeks 4–5 | Add three persona agents with UI selector; logging dashboard. |
| **P3** | Weeks 6+ | Evaluation harness, long‑term memory store, privacy enhancements. |
| **Future** | TBD | Voice I/O, calendar integration, export options, on‑device deployment. |
