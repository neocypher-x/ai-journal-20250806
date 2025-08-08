# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

This project uses Poetry for dependency management. Key commands:

- `poetry install` - Install dependencies and create virtual environment
- `poetry shell` - Activate virtual environment
- `poetry add <package>` - Add new dependency
- `poetry run <command>` - Run command in virtual environment

## Architecture Overview

This is an **Agentic AI Journal Reflection System** built as a stateless MVP using FastAPI and the OpenAI Agents SDK. The system processes journal entries and provides philosophically-grounded reflection prompts and advice.

### Core Design Pattern
- **Fan-out + merge orchestration**: Deterministic app-controlled workflow
- **Multi-agent system**: Each philosophical school (Buddhism, Stoicism, Existentialism) is a separate agent
- **Stateless**: No persistent memory or cross-session recall in MVP

### Key Components

1. **Orchestrator** (`/reflect` endpoint)
   - Validates input and attaches trace_id
   - Coordinates all agent calls
   - Handles errors and timeouts gracefully

2. **Journal Ingestor Agent**
   - Extracts summary, themes (≤5), and mood from journal text
   - Input: Raw markdown/text (300-1000 words typical)
   - Output: Structured data for downstream agents

3. **Philosophy Coach Agents** (3 agents)
   - `buddhist_coach`, `stoic_coach`, `existential_coach`
   - Process ingested content in parallel
   - Generate practical insights and actionable prompt suggestions

4. **Response Composer** (deterministic code)
   - Merges agent outputs intelligently
   - Deduplicates similar prompts using Jaccard similarity
   - Prioritizes by theme relevance and ensures balance (≤2 prompts per agent, max 5 total)
   - Generates final advice (≤120 words)

### API Contract

**Endpoint**: `POST /reflect`

**Request**:
```json
{
  "journal_text": "string, required",
  "question": "string, optional" 
}
```

**Response**:
```json
{
  "summary": "string (<=120 words)",
  "themes": ["string", "..."], 
  "mood": "calm|tense|stressed|sad|angry|energized|mixed",
  "prompts": [
    {
      "text": "actionable reflection prompt",
      "source": "buddhist|stoic|existential",
      "rationale": "short why"
    }
  ],
  "advice": "brief, concrete guidance (<=120 words)",
  "warnings": ["string (optional)"],
  "trace_id": "uuid"
}
```

## Configuration & Feature Flags

The system uses environment-based configuration:

- `MODELS.INGESTOR` - Model for journal ingestion
- `MODELS.COACH` - Model for philosophy coach agents  
- `FEATURES.LLM_ORCHESTRATOR` - Toggle for LLM-based composer (default: off)
- `LIMITS.MAX_PROMPTS` - Maximum prompts in response (default: 5)
- `LIMITS.AGENT_TIMEOUT_SEC` - Per-agent timeout (default: 8s)
- `LIMITS.GLOBAL_TIMEOUT_SEC` - Global request timeout (default: 25s)
- `LOGGING.REDACT_INPUTS` - Redact journal content in logs (default: on)

## Error Handling Strategy

- **Per-agent timeouts**: Failed agents are skipped, warnings added to response
- **Graceful degradation**: If journal ingestor fails, return 502 with clear message
- **Retries**: Single retry with jitter for 5xx model API errors
- **Input validation**: 400 for empty or oversized journal text (>10k chars)

## Performance Targets (MVP)

- p50 latency: ≤5-7s
- p95 latency: ≤15-20s  
- Target availability: 99% during testing

## Security Considerations

- Raw journal text never stored in logs (only hashes and metadata)
- Local deployment acceptable for MVP
- Rate limiting per IP via simple middleware
- HTTPS required for remote deployment

## Testing Strategy

Focus areas for testing:
- Schema validation for all agent inputs/outputs
- Deduplication logic edge cases
- Prioritization and balancing algorithms
- Timeout and failure scenarios
- Load testing with 50-100 concurrent requests

## Development Workflow

Since this is early-stage development, expect:
1. Iterative experimentation with agent prompts
2. Schema evolution as requirements clarify  
3. Performance tuning based on real usage patterns
4. Potential migration from code-based to LLM-based orchestration via feature flags