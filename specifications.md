# Agentic AI Journal Reflection System – Specifications (MVP — Stateless)

## 1. Purpose & Scope
- **Primary outcome**: Provide actionable, philosophically grounded reflection prompts and advice based on user journal content.
- **Secondary outcome**: Maintain a stateless design for MVP, with no cross-session recall.
- **Philosophical scope**: Core grounding in **Buddhism**, **Stoicism**, and **Existentialism**. Optional **Philosophy Scout** agent proposes relevant ideas from other schools when applicable.
- **Interaction style**: Conversational only (no proactive nudges in MVP).
- **Use cases**:
  - Daily reflection check-ins
  - Ad-hoc philosophical conversations related to journal content

## 2. User & Context
- **User base**: Single user (Chris)
- **Session frequency**:
  - Daily check-in (at least once/day)
  - On-demand ad-hoc queries

## 3. Journal Ingestion
- **Input formats**: Markdown (.md) or plain text (.txt)
- **Source**: Local file system (potential cloud integration later)
- **Ingestion cadence**: Real-time processing upon save or upload
- **Entry size**: 300–1000 words typical
- **Processing tasks**:
  - Summarization
  - Thematic extraction
  - Mood/energy tagging
  - Action item detection

## 4. Conversation & Behavior
- **Tone**: Can shift between Socratic questioning and direct guidance.
- **Depth levels**:
  - Surface-level observations
  - Text-cited analysis (when needed)
- **Boundaries**: No excluded topics for MVP.
- **Proactivity**: None in MVP (user-initiated).

## 5. Personalization
- **Core virtues to emphasize**: Freedom, respect
- **Practices**: None predefined (to be discovered through use)
- **Hard "no’s"**: None for MVP

## 6. Knowledge & Citations
- **Citation requirement**: Not required for MVP
- **Knowledge base**:
  - Philosophy & modern psychology (CBT/ACT)
  - No private library integration initially

## 7. Safety, Privacy & Data Handling
- **Storage**: Local storage only for MVP
- **Retention**: All data kept unless manually deleted
- **Security**: No encryption for MVP (possible in future)
- **Audit logs**: Conversation and processing logs stored locally

## 8. Capabilities & Tools
- **State**: Stateless (no persistent memory in MVP)
- **Tools**: None in MVP (future expansion possible)
- **Multimodal**: Text only for MVP
- **Offline mode**: Not required

## 9. System Design
- **Architecture**: Multi-agent system:
  - **Journal Ingestor** → prepares summaries, themes, mood
  - **Core Philosophical Agents** (Buddhism, Stoicism, Existentialism)
  - **Philosophy Scout Agent** (optional) → suggests other schools where relevant
  - **Orchestrator** → routes and merges responses
- **Model baseline**: gpt-4o-mini
- **Retrieval strategy**: None in MVP (no RAG)
- **Prompting strategy**: Iterative experimentation allowed
- **Additional technologies**: FastAPI, OpenAI Agents SDK
- **Error handling**: Minimal fallback behavior if ingestion or processing fails

## 10. UX & Product Surface
- **Interfaces**:
  - MVP: CLI or API endpoints
  - Later: Web app, possibly mobile
- **Session types**: One unified reflection session type for MVP
- **Notifications**: None in MVP
- **Accessibility**: None in MVP

## 11. Evaluation & Telemetry
- **Metrics**:
  - User-provided rubric scoring
  - Thumbs up/down feedback
- **Red-teaming**: Basic manual evaluation in MVP

## 12. Legal & Ethics
- **Licensing**: TBD for philosophical texts
- **Data processing agreements**: Not applicable in MVP

## 13. Delivery & Roadmap
### MVP
1. Ingest Markdown or plain-text journals
2. Multi-agent conversation engine generates:
   - Reflection prompts
   - Philosophical guidance
3. Minimal error handling for failed ingestions or processing  
   *(Stateless MVP: no memory, no RAG)*

### Future Phases
- Advanced orchestration & reasoning strategies
- Cloud sync & encryption
- Notifications & proactive prompts
- Expanded philosophical corpus
- Voice & multimodal input

## 14. Architecture (MVP — Stateless)

```

+------------------+
|   CLI / API      |
| (user request)   |
+---------+--------+
          |
          v
+---------------------------+
|        Orchestrator       |
| - validates input         |
| - routes workflow         |
| - merges agent outputs    |
| - handles errors          |
+----+----------+-----------+
     |          |
     |          v
     |   +-----------------------+
     |   |   Journal Ingestor    |
     |   | - parse .md/.txt      |
     |   | - light cleanup       |
     |   | - summary/themes/mood |
     |   +-----------+-----------+
     |               |
     |    summarized context
     |               v
     |   +-----------------------+      +-------------------------+
     |   | Core Philosophical    |      |   Philosophy Scout      |
     |   | Agents (stateless):   |      | (optional in MVP)       |
     |   | - Buddhism            |      | - probes other schools  |
     |   | - Stoicism            |      |   if clearly relevant   |
     |   | - Existentialism      |      +------------+------------+
     |   +-----------+-----------+                   |
     |               |                               |
     +---------------+---------------+---------------+
                     |
                     v
           +-------------------------+
           |   Response Composer     |
           | - reconcile viewpoints  |
           | - generate prompts      |
           | - actionable advice     |
           +------------+------------+
                        |
                        v
           +-------------------------+
           |  Output Formatter       |
           |  (JSON/text)            |
           +-------------------------+

Notes:
- Stateless MVP: no persistent memory, no cross-session recall, no RAG.
- Inputs: current journal entry (300–1000 words) and/or ad-hoc question.
- Errors: ingestion/parse failures return a clear message and are logged locally.
```

```mermaid
flowchart TD
    UI[CLI / API] --> ORCH[Orchestrator\nvalidate • route • merge • errors]

    ORCH --> ING[Journal Ingestor\nparse md/txt • cleanup • summary/themes/mood]

    ING --> CORE[Core Philosophical Agents\nBuddhism • Stoicism • Existentialism]
    ING --> SCOUT[Philosophy Scout (optional)\nprobe other schools if relevant]

    CORE --> COMP[Response Composer\nreconcile views • prompts • advice]
    SCOUT --> COMP

    COMP --> OUT[Output Formatter (JSON/text)]

    note1[[Stateless MVP: no memory, no RAG]]
    note2[[Error handling: graceful messages + local logs]]

    ORCH --- note1
    ORCH --- note2
```