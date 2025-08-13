# AI Journal Reflection System (v2)

A FastAPI-based agentic system for philosophical journal reflection that provides multi-perspective analysis of personal journal entries through Buddhist, Stoic, Existentialist, and NeoAdlerian frameworks.

## Overview

This system analyzes journal entries through **two complementary workflows**:

1. **One-Shot Reflection** (v1): Direct analysis and philosophical reflection
2. **Interactive Excavation** (v2): Socratic dialogue to identify root issues before generating reflections

The system generates philosophical reflections from multiple perspectives, synthesized by an Oracle meta-agent that identifies agreements, tensions, and provides unified guidance.

## Features

### Core Features
- **Multi-perspective Analysis**: Buddhist, Stoic, Existentialist, and NeoAdlerian philosophical frameworks
- **Optional Philosophy Scout**: Suggests additional relevant frameworks (CBT, ACT, Taoism, etc.)
- **Oracle Synthesis**: Meta-analysis identifying agreements, tensions, and unified guidance
- **Structured Output**: Complete reflections with perspectives and cross-framework synthesis
- **FastAPI Backend**: RESTful API with interactive documentation
- **React Frontend**: Modern web interface for journal entry submission and reflection viewing

### v2 Interactive Excavation
- **Socratic Dialogue**: AI-driven hypothesis testing through contrastive questions
- **Root Issue Identification**: Systematic excavation to find the core psychological issue
- **Evidence-Based Confidence**: Dynamic belief updating based on user responses
- **Multiple Exit Conditions**: Confidence threshold, confirmation votes, or budget limits
- **Stateless Design**: Client-driven state management for scalability

## Architecture

### Core Components

1. **Philosophical Agents**: Generate individual perspectives
   - Buddhist Agent
   - Stoic Agent  
   - Existentialist Agent
   - NeoAdlerian Agent
   - Philosophy Scout (optional)

2. **Excavation Engine** (v2): Interactive hypothesis testing
   - Hypothesis seeding from journal entries
   - Contrastive probe generation
   - Belief updating with structured outputs
   - Exit condition monitoring

3. **Oracle Agent**: Performs meta-analysis and synthesis of all perspectives

4. **Data Models**: Comprehensive Pydantic models for structured outputs

### Processing Flows

#### v1 One-Shot Flow
1. User submits journal entry via API
2. Each philosophical agent generates its perspective concurrently
3. Oracle analyzes all perspectives and generates prophecy
4. System returns complete reflection

#### v2 Interactive Flow
1. User initiates excavation with journal entry
2. System seeds 2-4 hypothesis candidates
3. **Interactive Loop**:
   - AI generates contrastive Socratic questions
   - User provides responses
   - System updates hypothesis confidence scores
   - Continue until exit conditions met
4. System identifies confirmed crux and secondary themes
5. Generate enhanced reflection based on excavation results

## Technology Stack

- **Framework**: FastAPI for API endpoints
- **Package Management**: Poetry (pyproject.toml configuration)
- **Python Version**: >=3.12
- **AI Model**: gpt-5-nano (base model)
- **Structured Outputs**: OpenAI's native Pydantic integration
- **Key Dependencies**: 
  - `openai` for AI model integration
  - `fastapi` and `uvicorn` for web API
  - `pydantic` for data models and structured outputs
  - `doppler-env` for environment management

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry
- OpenAI API key
- Doppler CLI (for environment management)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables via Doppler or create `.env` file:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   ```

### Running the Server

```bash
# With Doppler (recommended)
doppler -p ai-journal -c dev run -- poetry run uvicorn ai_journal.main:app --reload

# Or directly with Poetry
poetry run uvicorn ai_journal.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## API Usage

### v1 One-Shot Reflection

**POST** `/api/reflections`

```json
{
  "journal_entry": {
    "text": "Your journal entry text here..."
  },
  "enable_scout": false
}
```

### v2 Interactive Excavation

#### Start Excavation
**POST** `/api/excavations`

```json
{
  "mode": "init",
  "journal_entry": {
    "text": "I keep saying yes to work I don't want to do..."
  }
}
```

**Response:**
```json
{
  "complete": false,
  "state": {
    "state_id": "uuid",
    "revision": 1,
    "hypotheses": [
      {
        "hypothesis_id": "uuid",
        "text": "Fear of disappointing others drives automatic yes responses",
        "confidence": 0.40,
        "confirmations": 0,
        "status": "active"
      }
    ],
    "budget_used": 0
  },
  "next_probe": {
    "probe_id": "uuid", 
    "question": "When you imagine saying no to a request, what specifically worries you most?",
    "targets": ["hypothesis_id"]
  }
}
```

#### Continue Excavation
**POST** `/api/excavations`

```json
{
  "mode": "continue",
  "state": { "...": "entire state from previous response" },
  "user_reply": "I worry they'll think I'm not committed or reliable",
  "expected_probe_id": "uuid"
}
```

#### Generate v2 Reflection
**POST** `/api/v2/reflections`

```json
{
  "from_excavation": {
    "confirmed_crux": {
      "hypothesis_id": "uuid",
      "text": "Fear of disappointing others drives people-pleasing behavior", 
      "confidence": 0.85
    },
    "secondary_themes": [],
    "excavation_summary": {
      "exit_reason": "threshold",
      "reasoning_trail": "..."
    }
  },
  "enable_scout": false
}
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `MODEL`: AI model to use (default: gpt-5-nano)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: False)
- `LOG_LEVEL`: Logging level (default: DEBUG)

### v2 Excavation Parameters
- `TAU_HIGH`: Confidence threshold for exit (default: 0.80)
- `DELTA_GAP`: Margin to second-best for exit (default: 0.25)
- `N_CONFIRMATIONS`: Confirmation votes needed (default: 2)
- `K_BUDGET`: Maximum probe turns (default: 4)
- `MAX_HYPOTHESES`: Maximum concurrent hypotheses (default: 4)

## Development

### Testing

```bash
# Run all tests with Doppler
doppler -p ai-journal -c dev run -- poetry run pytest -v

# Run v2 specific tests
doppler -p ai-journal -c dev run -- poetry run pytest tests/test_v2_basic.py -v
```

### Mock Mode for Frontend Development

For rapid frontend development without API costs:

```bash
# Add ?mock=true to any API call
curl 'http://localhost:8000/api/reflections?mock=true' \
  --data '{"journal_entry": {"text": "test"}, "enable_scout": false}'
```

### Frontend Development

The React frontend is located in the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

## File Structure

```
ai-journal/
├── src/ai_journal/              # Main package
│   ├── agents.py                # Philosophical agents
│   ├── config.py                # Configuration management
│   ├── excavation.py            # v2 interactive excavation engine
│   ├── main.py                  # FastAPI application
│   ├── models.py                # Pydantic data models (v1 + v2)
│   ├── oracle.py                # Oracle meta-agent
│   └── service.py               # Orchestration service
├── frontend/                    # React frontend
├── tests/                       # Test suite
│   └── test_v2_basic.py        # v2 excavation tests
├── specifications.md            # v1 system specifications
├── v2-implementation-specifications.md  # v2 detailed specs
├── v2-completion-summary.md     # v2 implementation summary
├── pyproject.toml              # Poetry configuration
└── README.md                   # This file
```

## API Endpoints Summary

| Endpoint | Method | Purpose | Version |
|----------|--------|---------|---------|
| `/api/reflections` | POST | One-shot reflection generation | v1 (MVP) |
| `/api/excavations` | POST | Interactive excavation workflow | v2 |
| `/api/v2/reflections` | POST | Generate reflection from excavation | v2 |
| `/api/health` | GET | Health check | All |

## Data Models

### v1 Models
- **JournalEntry**: User's journal text
- **Perspective**: Single philosophical school analysis
- **Prophecy**: Oracle meta-analysis with agreements, tensions, synthesis
- **Reflection**: Complete analysis containing perspectives + prophecy

### v2 Excavation Models
- **CruxHypothesis**: Candidate root issue with confidence tracking
- **Probe**: Contrastive Socratic question for hypothesis testing
- **ExcavationState**: Server-canonical state for interactive sessions
- **ExcavationResult**: Final validated crux with secondary themes

## Philosophical Frameworks

### Core Traditions
- **Buddhism**: Focus on reducing suffering through mindful awareness and impermanence
- **Stoicism**: Emphasis on virtue, rational control, and acceptance of what cannot be changed  
- **Existentialism**: Stress on authentic choice, freedom, and personal responsibility
- **NeoAdlerianism**: Individual psychology focusing on social interest and goal orientation

### Philosophy Scout
When enabled, the Scout agent can identify and invoke additional relevant philosophical traditions based on the specific themes in your journal entry.

## v2 Interactive Excavation Process

The v2 system implements a **Contrastive Socratic Agent (CSA)** - a statechart-controlled, hypothesis-testing ReAct variant with specialist synthesis:

1. **Hypothesis Seeding**: Extract 2-4 candidate root issues using AI analysis
2. **Interactive Probing**: Generate contrastive questions to distinguish hypotheses
3. **Belief Updating**: Update confidence scores based on user responses using structured outputs
4. **Exit Conditions**: Multiple criteria (confidence threshold, confirmations, budget)
5. **Enhanced Reflection**: Generate focused philosophical perspectives based on confirmed crux

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality  
3. Update documentation as needed
4. Ensure all tests pass before submitting
5. For v2 features, test both interactive excavation and reflection generation

## Troubleshooting

### Common Issues

**API connection issues:**
- Verify OpenAI API key is set correctly
- Check Doppler configuration: `doppler secrets`
- Ensure server is running on the expected port

**v2 Excavation issues:**
- Check confidence scores are updating in responses
- Verify structured outputs are being parsed correctly
- Review excavation state progression through revisions

**Test failures:**
- Verify API key is available for integration tests
- Use `doppler -p ai-journal -c dev run -- poetry run pytest -v` for full test suite

## License

[License details to be determined]

## Acknowledgments

Built with inspiration from classical philosophical traditions and modern AI capabilities to help people reflect more deeply on their experiences and challenges. v2 adds interactive Socratic dialogue capabilities for deeper psychological exploration.