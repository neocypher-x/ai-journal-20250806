# MVP Specification – Philosophical Reflection Assistant (No Vector DB, v1.1)

**Revision Date:** 2025‑08‑06
**Author:** Chris (Product Manager / Founder)

---

## 1  Purpose

Deliver a minimal, production‑ready web service that ingests a single journal entry and returns a set of reflective questions and/or actionable advice grounded in three philosophical schools—Stoicism, Buddhism, and Existentialism—without relying on a vector database or long‑term memory. This MVP validates core user value (quality of reflections) while keeping infrastructure and ops overhead close to zero.

---

## 2  Scope

### 2.1  In Scope

* **Single‑entry reflection**: One journal entry per request.
* **Multi‑agent reasoning**: Dedicated LLM agent per school of thought.
* **Synchronous API**: HTTP POST endpoint (`/reflect`).
* **Stateless operation**: No persistent user data; no embeddings or vector store.
* **Web demo UI**: Simple textarea + response panel.

### 2.2  Out of Scope

* Long‑term memory or user profiles.
* Quote/citation grounding via external corpus.
* Mobile app, push notifications, or weekly digest.
* Crisis detection / safety classification beyond OpenAI policy defaults.

---

## 3  Personas & Use Cases

| Persona                            | Goal                                                    | Success Metric                                |
| ---------------------------------- | ------------------------------------------------------- | --------------------------------------------- |
| **Introspective Knowledge Worker** | Gain fresh perspectives on a recent experience          | Rates reflection ≥ 4 / 5                      |
| **Mental‑Fitness Enthusiast**      | Compare philosophical angles on a tough thought pattern | Finds at least one prompt "personally useful" |

---

## 4  Functional Requirements (FR)

| ID       | Description                                                                                 | Priority |
| -------- | ------------------------------------------------------------------------------------------- | -------- |
| **FR‑1** | API accepts a UTF‑8 journal entry (`string`, ≤ 1 500 tokens)                                | P0       |
| **FR‑2** | Router dispatches entry to three agents: Stoic, Buddhist, Existentialist                    | P0       |
| **FR‑3** | Each agent returns 2‑3 reflective **questions** *and* 1 short **advice** snippet in JSON    | P0       |
| **FR‑4** | Mixer aggregates agents' outputs, deduplicates similar items (≥ 0.8 Jaccard), returns top 5 | P0       |
| **FR‑5** | Front‑end renders response                                    | P1       |

---

## 5  System Architecture

```text
Client (React)
   │  POST /reflect (journal_entry)
   ▼
FastAPI Server  ──▶  Router/Mixer  ──┬─▶  StoicAgent (GPT‑4o)
                                    ├─▶  BuddhistAgent (GPT‑4o)
                                    └─▶  ExistentialistAgent (GPT‑4o)
```

* **Agents run in parallel** via `asyncio.gather()` or Agents SDK `Runner.run_async`.
* **Router/Mixer** merges the three JSON payloads, removes duplicates, limits to max 5 items.
* **Stateless**: no DB containers, only ephemeral request context.

---

## 6  Prompt Design (per agent)

```text
SYSTEM:
You are a {school} mentor. Write in the characteristic tone of {school} philosophy.

USER:
Here is a personal journal entry. Reflect upon it.

ASSISTANT_INSTRUCTIONS:
Return a JSON array with objects:
{
  "school": "Stoic",    // constant
  "questions": ["...", "..."], // 2‑3 open‑ended, first‑person
  "advice": "..."               // ≤ 40 words, imperative mood
}
```

`temperature = 0.4`, `top_p = 1`, `max_tokens = 300`.

---

## 7  API Contract

**Endpoint**: `POST /reflect`

**Request**

```json5
{
  "journal_entry": "string  =<1500 tokens"
}
```

**Success Response (200)**

```json5
{
  "reflections": [
    {
      "school": "Stoic",
      "questions": [ "Q1", "Q2" ],
      "advice": "..."
    },
    {
      "school": "Buddhist",
      "questions": [ "Q1", "Q2" ],
      "advice": "..."
    },
    {
      "school": "Existentialist",
      "questions": [ "Q1", "Q2" ],
      "advice": "..."
    }
  ]
}
```

**Error Response (4xx/5xx)** – JSON with `message` field.

---

## 8  Tech Stack

| Layer             | Choice                                          | Rationale                                                               |
| ----------------- | ----------------------------------------------- | ----------------------------------------------------------------------- |
| **LLM**           | OpenAI GPT‑4o (2025‑06)                         | Best‑in‑class reasoning, function calling                               |
| **Orchestration** | **OpenAI Agents SDK** (alt: Smolagents or Agno) | Lightweight, production‑ready; avoid LangGraph/LangSmith per preference |
| **API**           | FastAPI (Python 3.11)                           | Async‑first, type hints                                                 |
| **Frontend**      | Next.js 14 + Tailwind                           | Rapid prototyping                                                       |
| **Hosting**       | Fly.io / Vercel                                 | Quick deploy, SSL by default                                            |

---

## 9  Logging & Metrics

* **Ingestion**: `request_id`, request size, start\_time.
* **Per agent**: tokens\_in/out, latency\_ms, cost\_usd.
* **Mixer**: duplicates\_removed count.
* **Overall**: p50/p95 latency, error rate.

Logs stored in CloudWatch / S3 with a 7‑day retention by default.

---

## 10  Acceptance Criteria

1. POSTing a 500‑word entry returns ≤ 5 reflections within 2 s p95.
2. Each reflection JSON block passes JSON schema validation.
3. Deduplication removes identical questions across schools.
4. Front‑end renders labeled accordions for each school.
5. Unit tests cover: router logic, schema compliance, deduplication util.

---

## 11  Open Issues / Future Enhancements

* Add vector‑based retrieval for grounded quotes.
* Persist user sessions for longitudinal insights.
* Auto‑router that chooses best school based on entry content.
* Safety NLP pass for crisis language detection.

---

## 12  Timeline (9‑day sprint)

| Day | Milestone                               |
| --- | --------------------------------------- |
| 1   | Repo scaffold, FastAPI endpoint stub    |
| 2   | Implement Stoic agent end‑to‑end        |
| 3   | Clone Buddhist & Existentialist agents  |
| 4   | Parallel execution + Mixer + dedup util |
| 5   | JSON schema & validation tests          |
| 6   | Basic React UI (textarea + display)     |
| 7   | Telemetry hooks (latency, tokens)       |
| 8   | Internal QA with 20 sample entries      |
| 9  | Deploy to staging; produce demo video   |

---

**End of document**
