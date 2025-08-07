Below is a **concise architectural overview** of the backend when you build the MVP on top of **OpenAI Agents SDK**. The goal is to show where each concern lives, how requests flow, and what you actually have to write.

---

## 1 High-level component diagram

```text
┌───────────────┐  POST /reflect
│  Front-end    │────────────────────────────────┐
└───────────────┘                                │
                                                 ▼
                          ┌─────────────────────────────────┐
                          │     FastAPI / ASGI Layer        │
                          │  • Input validation (Pydantic)  │
                          │  • Rate/size limits             │
                          └─────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────────────┐
                          │  Router / Mixer (Python func)   │
                          ├─────────────────────────────────┤
                          │ async gather(                   │
                          │   StoicAgent.run_async(),       │
                          │   BuddhistAgent.run_async(),    │
                          │   ExistentialistAgent.run_async())│
                          └─────────────────────────────────┘
                               ▲            ▲            ▲
             ┌─────────────────┴────────────┴────────────┴─────────────────┐
             │                         Agents                               │
             │  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
             │  │ StoicAgent   │ │ BuddhistAgent│ │ ExistentialistAgent │  │
             │  │ • prompt     │ │ • prompt     │ │ • prompt            │  │
             │  │ • tools=[]   │ │ • tools=[]   │ │ • tools=[]          │  │
             │  └──────────────┘ └──────────────┘ └─────────────────────┘  │
             └──────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────────────┐
                          │     Response assembler          │
                          │  • de-dup questions             │
                          │  • enforce max=5 items          │
                          └─────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────────────┐
                          │         JSON Response           │
                          └─────────────────────────────────┘
```

**Key points**

* **Stateless** – every request goes through the same path; nothing is cached or stored.
* **Fan-out / fan-in** – the Router function does a parallel *fan-out* to three Agents, then *fan-in* the results.
* **Single external dependency** – OpenAI REST calls made via Agents SDK; no DB, queue, or file storage.

---

## 2 Modules you actually code

| Module                                       | Responsibility                                              | Important calls                         |
| -------------------------------------------- | ----------------------------------------------------------- | --------------------------------------- |
| **`main.py`**                                | FastAPI app, `/reflect` route, global `OpenAI` client init  | `asyncio.gather`, `Router.reflect()`    |
| **`router.py`**                              | Build agent tasks, run them concurrently, merge output      | `Runner.run_async`, custom `dedup()`    |
| **`agents/stoic.py`** *(similar for others)* | `Agent` object with prompt template & schema definition     | `agent = Agent(prompt=..., schema=...)` |
| **`schemas.py`**                             | Pydantic models for request, per-agent JSON, final response | Validation & OpenAPI docs               |
| **`metrics.py`**                             | Log tokens, latency, cost to stdout / CloudWatch            | Decorator around agent calls            |

Only \~250 lines of **real** code + 3 prompt strings.

---

## 3 Sequence diagram (runtime view)

1. **Client** → `POST /reflect` with journal text.
2. **FastAPI handler**

   * validates size ≤ 1 500 tokens
   * starts latency timer
3. **Router.reflect()** builds three **Task** objects: `(StoicAgent, journal)`, `(BuddhistAgent, …)`, `(ExistentialistAgent, …)`.
4. `await Runner.run_async(tasks, concurrency=3)`

   * Agents SDK handles retries, streaming, JSON output validation.
5. **Fan-in**: Collect results → `dedup()` (Jaccard ≥ 0.8) → truncate to 5.
6. Assemble final JSON, log tokens/latency, return 200.
7. **FastAPI** finishes, timer stops → metrics sink.

**p95 latency budget**

| Phase                                 | Typical time (ms) |
| ------------------------------------- | ----------------- |
| Validation + pre-work                 | 10                |
| 3× agent calls (parallel, worst-case) | \~1 400           |
| Merge + serialization                 | 30                |
| **Total**                             | **\~1 450 ms**    |

Plenty of headroom under the 2 s target.

---

## 4 OpenAI Agents SDK specifics

* **Parallelism** – `Runner.run_async()` accepts a list of “agent + inputs” tuples and executes them concurrently with an internal connection pool.
* **Schema enforcement** – Define JSON schema once in each Agent; SDK validates the LLM output so your Mixer receives correct JSON or an explicit failure.
* **Error strategy** –

  * *Timeout* → SDK raises `AgentTimeout`; Router catches and replaces that agent’s block with a generic “Sorry, Stoic reflections unavailable.”
  * *ValidationError* → Router retries once with higher temperature, then fails gracefully.
* **Streaming** – Optional (`stream=True`); you can start sending reflections back to the UI while other agents finish, but for simplicity you can aggregate first.

---

## 5 Operational envelope

* **Scaling** – Deploy under Fly.io with `--min=1 --max=3` machines; each is stateless and independent.
* **Memory** – Each worker ≈ 200 MB RAM (Python + models + overhead).
* **Secrets** – Store `OPENAI_API_KEY` in Fly secrets; no other credentials needed.
* **Cost guardrail** – Global `max_tokens=300` per agent; log cost and rate-limit to e.g. 30 requests/min across fleet.

---

## 6 Extending later

| Feature                  | Change required                                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Add vector retrieval** | Inject a `retrieve()` step before agent call; pass passages via `tools=[context_tool]` in the Agent definition. |
| **Long-term memory**     | Replace FastAPI handler with small orchestration graph (`Planner`) + external KV store; rest of stack stays.    |
| **More personas**        | Add new Agent file + tag to Router list; no infra change.                                                       |

---

### Bottom line

With **OpenAI Agents SDK** the backend is a **thin FastAPI shell plus a router module** that fans out to three agents concurrently and merges their validated JSON outputs. No state, no extra infra, predictable latency, and an easy path to richer features later.
