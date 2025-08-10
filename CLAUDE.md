# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an agentic AI journal system that provides philosophical reflections on user journal entries. The system uses multiple philosophical agents (Buddhist, Stoic, Existentialist) plus an optional Philosophy Scout to analyze journal entries from different philosophical perspectives, then synthesizes insights via an Oracle meta-agent.

## Technology Stack

- **Framework**: FastAPI for API endpoints
- **Package Management**: Poetry (pyproject.toml configuration)
- **Python Version**: >=3.12
- **AI Model**: gpt-5-nano (base model)
- **Key Dependencies**: 
  - `openai` for AI model integration
  - `fastapi` and `uvicorn` for web API
  - `pydantic` for data models and structured outputs
  - `doppler-env` for environment management

## Development Commands

Since this project uses Poetry for dependency management:

```bash
# Install dependencies
poetry install

# Run the FastAPI application
poetry run uvicorn ai_journal.main:app --reload

# Access interactive API docs
# http://localhost:8000/docs (when server is running)
```

## Architecture

### Core Components

The system follows a multi-agent architecture with these key entities:

1. **Philosophical Agents**: Generate individual perspectives
   - Buddhist Agent
   - Stoic Agent  
   - Existentialist Agent
   - Philosophy Scout (optional) - proposes additional relevant schools

2. **Oracle Agent**: Performs meta-analysis and synthesis of all perspectives

3. **Data Models**: Comprehensive Pydantic models for structured outputs (see mvp-implementation-specifications.md)

### Key Models Structure

- `JournalEntry`: User input text (300-1000 words typical)
- `Perspective`: Output from a single philosophical school containing:
  - Core principle invoked
  - Challenge framing
  - Practical experiment
  - Potential trap/misinterpretation
  - Key metaphor
- `Prophecy`: Cross-school meta-analysis from Oracle including:
  - Agreement scorecard (pairwise school comparisons)
  - Tension summary
  - Synthesis
  - What is lost by blending
- `Reflection`: Top-level container with Perspectives + Prophecy

### API Design

**Primary Endpoint**: `POST /reflections`
- Input: `ReflectionRequest` with journal entry text and optional philosophy scout flag
- Output: `ReflectionResponse` containing complete philosophical reflection

### Processing Flow

1. User submits journal entry via API
2. Each philosophical agent generates its perspective concurrently
3. Oracle analyzes all perspectives and generates prophecy
4. System returns complete reflection with all perspectives and meta-analysis

## Development Guidelines

- Use structured outputs with Pydantic models throughout
- The system is stateless - each journal entry processed in isolation
- Follow the detailed model specifications in `mvp-implementation-specifications.md`
- Maintain philosophical authenticity - each agent should embody its tradition
- All responses should include practical, actionable elements

## File Structure

- `src/ai_journal/`: Main package directory
- `mvp-implementation-specifications.md`: Detailed technical specifications and Pydantic models
- `specifications.md`: High-level system requirements and architecture
- `pyproject.toml`: Poetry configuration with dependencies

## Current Status

This appears to be an early-stage project with core specifications defined but implementation in progress. The main source directory contains only the package initialization file.