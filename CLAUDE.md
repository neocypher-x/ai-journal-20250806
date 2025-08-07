# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the AI Journal project - an agentic AI system that provides philosophical reflection and advice based on personal journal entries. The system uses multiple AI agents representing different philosophical schools (Stoicism, Buddhism, Existentialism) to analyze journal content and provide personalized insights.

## Architecture

The project follows a multi-agent architecture pattern:

### Core Components
- **Router/Mixer**: Central orchestration component that fans out journal entries to multiple philosophical agents in parallel, then aggregates and deduplicates their responses
- **Philosophical Agents**: Three specialized agents (StoicAgent, BuddhistAgent, ExistentialistAgent) that each provide reflective questions and advice from their respective philosophical perspectives
- **FastAPI Backend**: Stateless API server with `/reflect` endpoint for processing journal entries
- **Response Processing**: Deduplication system using Jaccard similarity (≥ 0.8 threshold) to remove similar questions across agents

### Technical Stack
- **LLM**: OpenAI GPT-4o via OpenAI Agents SDK
- **API Framework**: FastAPI with async support
- **Frontend**: Next.js 14 + Tailwind CSS (planned)
- **Orchestration**: OpenAI Agents SDK for parallel agent execution
- **Hosting**: Fly.io / Vercel deployment target

## Development Setup

This project uses the Python development stack documented in `init-python-project-doc.md`:

### Prerequisites
- Python 3.12.8 (managed via pyenv)
- Poetry for dependency management
- Doppler for secrets management

### Initial Setup
```bash
# Set Python version
pyenv local 3.12.8

# Configure Poetry for in-project virtual environments
poetry config virtualenvs.in-project true

# Install dependencies
poetry install

# Add doppler-env package for secrets injection
poetry add doppler-env

# Enter virtual environment
poetry shell
```

### Development Commands
Since this is a planning/specification repository, there are no build, test, or lint commands yet. The actual implementation will follow the MVP specifications outlined in the documentation.

## Key Specifications

### API Contract
- **Endpoint**: `POST /reflect`
- **Input**: Journal entry (≤ 1,500 tokens)
- **Output**: Up to 5 philosophical reflections with questions and advice
- **Performance Target**: p95 latency ≤ 2 seconds

### Agent Response Format
Each agent returns JSON with:
```json
{
  "school": "Stoic|Buddhist|Existentialist",
  "questions": ["question1", "question2"],
  "advice": "short advice snippet (≤40 words)"
}
```

### System Constraints
- Stateless operation (no persistent storage)
- Parallel agent execution via `asyncio.gather()` or `Runner.run_async()`
- Maximum 5 reflections returned after deduplication
- Rate limiting and cost guardrails for OpenAI API usage

## Implementation Timeline

Based on `mvp-specifications.md`, the 9-day development sprint:
1. Day 1: Repo scaffold, FastAPI endpoint stub
2. Day 2: Implement Stoic agent end-to-end
3. Day 3: Clone Buddhist & Existentialist agents
4. Day 4: Parallel execution + Mixer + dedup util
5. Day 5: JSON schema & validation tests
6. Day 6: Basic React UI (textarea + display)
7. Day 7: Telemetry hooks (latency, tokens)
8. Day 8: Internal QA with 20 sample entries
9. Day 9: Deploy to staging; produce demo video

## Future Extensions

The architecture is designed to support:
- Vector retrieval for grounded quotes from canonical texts
- Long-term memory via external KV store
- Additional philosophical personas
- Crisis detection and safety classification