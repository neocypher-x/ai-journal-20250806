# AI Journal Reflection System

An agentic AI journal system that provides philosophical reflections on user journal entries. The system uses multiple philosophical agents (Buddhist, Stoic, Existentialist) plus an optional Philosophy Scout to analyze journal entries from different philosophical perspectives, then synthesizes insights via an Oracle meta-agent.

## Features

- **Multi-Philosophical Analysis**: Get perspectives from Buddhist, Stoic, and Existentialist traditions
- **Philosophy Scout**: Optionally discover additional relevant philosophical schools
- **Oracle Synthesis**: Meta-analysis revealing agreements, tensions, and unified wisdom
- **Modern Web Interface**: Clean, zen-inspired React frontend with responsive design
- **RESTful API**: FastAPI backend with comprehensive OpenAPI documentation
- **Comprehensive Testing**: Full test suite with unit and integration tests

## Architecture

### Technology Stack

- **Backend**: FastAPI + Python 3.12+
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS + shadcn/ui components
- **AI Model**: OpenAI GPT (configurable model)
- **Package Management**: Poetry for Python dependencies, npm for frontend
- **Environment Management**: Doppler for secrets and configuration
- **Testing**: pytest with async support

### System Components

1. **Philosophical Agents**: Generate individual perspectives
   - Buddhist Agent
   - Stoic Agent  
   - Existentialist Agent
   - Philosophy Scout (optional) - proposes additional relevant schools

2. **Oracle Agent**: Performs meta-analysis and synthesis of all perspectives

3. **Web Interface**: React frontend with journal entry form and reflection display

4. **API Layer**: FastAPI endpoints for reflection generation and frontend serving

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Node.js 18+ (managed with nvm recommended)
- Poetry for Python dependency management
- Doppler CLI for environment management
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-journal
   ```

2. **Install Python dependencies:**
   ```bash
   poetry install
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment:**
   - Set up your Doppler project with OpenAI API key
   - Or create a `.env` file with required variables (see Configuration section)

### Configuration

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DEBUG`: Set to `true` for debug logging (optional)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR) (optional)
- `MODEL`: OpenAI model to use (default: gpt-4o-mini) (optional)

## Usage

### Running the Application

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

2. **Start the server:**
   ```bash
   # With Doppler (recommended)
   doppler -p ai-journal -c dev run -- poetry run uvicorn ai_journal.main:app --reload

   # Or directly (ensure environment variables are set)
   poetry run uvicorn ai_journal.main:app --reload
   ```

3. **Access the application:**
   - **Web Interface**: http://localhost:8000/
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/api/health

### Using the Web Interface

1. Navigate to http://localhost:8000/
2. Enter your journal entry (50-1000 words recommended)
3. Optionally enable Philosophy Scout for additional perspectives
4. Click "Get Reflection" to generate your philosophical analysis
5. Explore the perspectives and oracle synthesis
6. Use "New Reflection" to analyze another entry

### Using the API

**Generate Reflection:**
```bash
curl --request POST \
  --url http://localhost:8000/api/reflections \
  --header 'Content-Type: application/json' \
  --data '{
    "journal_entry": {
      "text": "Your journal entry text here..."
    },
    "enable_scout": false
  }'
```

**Health Check:**
```bash
curl http://localhost:8000/api/health
```

## Development

### Development Workflow

1. **Backend Development:**
   ```bash
   # Run with auto-reload
   doppler -p ai-journal -c dev run -- poetry run uvicorn ai_journal.main:app --reload
   ```

2. **Frontend Development:**
   ```bash
   cd frontend
   # Development server with API proxy
   npm run dev
   ```

3. **Building for Production:**
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

### Running Tests

**All tests:**
```bash
doppler -p ai-journal -c dev run -- poetry run pytest -v
```

**Unit tests only (no API calls):**
```bash
poetry run pytest tests/ -k "not slow" -v
```

**Single test file:**
```bash
doppler -p ai-journal -c dev run -- poetry run pytest tests/test_example.py -v
```

**Using VSCode Test Configurations:**
- Use the "Test: All Tests" launch configuration
- Or "Test: Current File" for focused testing

### Project Structure

```
ai-journal/
├── src/ai_journal/          # Python backend
│   ├── __init__.py
│   ├── main.py             # FastAPI app with frontend serving
│   ├── models.py           # Pydantic data models
│   ├── agents.py           # Philosophical agents
│   ├── oracle.py           # Oracle meta-agent
│   ├── service.py          # Main service orchestration
│   └── config.py           # Configuration management
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── lib/           # Utilities and API client
│   │   ├── types/         # TypeScript type definitions
│   │   └── App.tsx        # Main React app
│   ├── package.json
│   └── vite.config.ts     # Vite configuration
├── tests/                 # Test suite
├── static/               # Built frontend assets (auto-generated)
├── pyproject.toml        # Poetry configuration
└── README.md
```

### API Endpoints

- `GET /` - Serve React frontend
- `GET /api/health` - Health check
- `POST /api/reflections` - Generate philosophical reflection
- `GET /docs` - Interactive API documentation
- `GET /{path:path}` - Catch-all for React router

## Data Models

### Input Models
- **JournalEntry**: User's journal text
- **ReflectionRequest**: Journal entry + scout enable flag

### Output Models
- **Perspective**: Single philosophical school analysis with:
  - Framework identification
  - Core principle invoked
  - Challenge framing
  - Practical experiment
  - Potential trap
  - Key metaphor

- **Prophecy**: Oracle meta-analysis with:
  - Agreement scorecard (pairwise framework comparisons)
  - Tension summary (philosophical conflicts)
  - Synthesis (unified wisdom)
  - What is lost by blending (trade-offs)

- **Reflection**: Complete analysis containing perspectives + prophecy

## Philosophical Frameworks

### Core Traditions
- **Buddhism**: Focus on reducing suffering through mindful awareness and compassion
- **Stoicism**: Emphasis on virtue, rational control, and acceptance of what cannot be changed  
- **Existentialism**: Stress on authentic choice, freedom, and personal responsibility

### Philosophy Scout
When enabled, the Scout agent can identify and invoke additional relevant philosophical traditions based on the specific themes in your journal entry.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`doppler -p ai-journal -c dev run -- poetry run pytest -v`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Common Issues

**Frontend build errors:**
- Ensure Node.js 18+ is installed
- Delete `node_modules` and `package-lock.json`, then `npm install`
- Check for TypeScript errors in the console

**API connection issues:**
- Verify OpenAI API key is set correctly
- Check Doppler configuration: `doppler secrets`
- Ensure server is running on the expected port

**Test failures:**
- Verify API key is available for integration tests
- Check that all dependencies are installed: `poetry install`
- Use `pytest -v -s` for more detailed test output

**Debug logging not appearing:**
- Set `DEBUG=true` in your environment
- Or set `LOG_LEVEL=DEBUG`
- Verify logging configuration in the FastAPI startup

### Getting Help

1. Check the [API documentation](http://localhost:8000/docs) when server is running
2. Review test files in `tests/` for usage examples
3. Check server logs for detailed error information
4. Verify environment configuration with `doppler secrets`

## License

[Add your license information here]

## Acknowledgments

Built with inspiration from classical philosophical traditions and modern AI capabilities to help people reflect more deeply on their experiences and challenges.