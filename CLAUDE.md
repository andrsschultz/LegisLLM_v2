# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
- **Full application**: `./run.sh` (starts both backend and frontend)
- **Backend only**: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- **Frontend only**: `streamlit run frontend/app.py --server.port 8501`
- **Install dependencies**: `pip install -r requirements.txt`

### Docker Operations
- **Build**: `docker build -t legisllm .`
- **Run**: `docker run -p 8501:8501 legisllm`

## Architecture Overview

LegisLLM is a German legal AI application with a **dual-architecture** design:

### Backend (FastAPI)
- **Location**: `/backend/`
- **Entry point**: `backend/main.py`
- **Core modules**:
  - `core/domain_logic.py` - Main AI logic for legal norm analysis
  - `core/llm_service.py` - LLM provider integration (OpenAI, DeepInfra)
  - `core/xml_parser.py` - German legal XML document parsing
  - `core/models.py` - Pydantic data models
  - `core/config.py` - Model configuration and enums
  - `core/auth.py` - API key authentication

### Frontend (Streamlit)
- **Location**: `/frontend/app.py`
- **Architecture**: Multi-step wizard interface with session state management
- **Core features**: 5-step legal drafting workflow

### API Endpoints
The backend provides these main endpoints:
- `/identify` - Single-step legal norm identification
- `/identify_multistep` - Multi-step reasoning for norm identification
- `/generate_proposals` - Generate amendment proposals
- `/evaluate_proposals` - Evaluate proposals against legal criteria
- `/deep_evaluate_proposals` - Detailed evaluation with juristic analysis
- `/amend` - Generate final amendment text

### Data Layer
- **Legal documents**: Stored as XML files in `/backend/data/`
- **Supported laws**: German tax law (EStG, UStG, GewStG, etc.)
- **Format**: XML with structured sections and paragraphs

## Key Design Patterns

### AI Provider Abstraction
- Models are configured in `core/config.py` with `ModelEnum`
- Provider detection via `is_deepinfra_model()` function
- API keys managed through environment variables

### Session State Management
- Frontend uses Streamlit session state extensively
- Each workflow step stores results for subsequent steps
- Tab navigation with state persistence

### Multi-step AI Reasoning
- Standard and multistep reasoning modes available
- Multistep mode breaks complex tasks into sub-tasks
- Configurable via frontend checkbox

## Environment Configuration

Required environment variables:
- `OPENAI_API_KEY` - For OpenAI models
- `DEEPINFRA_API_KEY` - For DeepInfra models  
- `BACKEND_URL` - Frontend-to-backend communication (default: http://localhost:8000)

## Development Notes

### XML Document Structure
German legal documents follow a specific XML schema with:
- `jurabk` - Law abbreviation (e.g., "EStG")
- `enbez` - Section designation (e.g., "§ 21")
- `P` - Paragraph/subsection number

### Model Selection
- Default model: GPT-3.5-turbo
- Reasoning models (o1, DeepSeek-R1) support multistep mode
- Provider is automatically detected based on model selection

### Logging and Debugging
- Frontend captures stdout to session state for debugging
- API calls are logged with endpoint, status, and response length
- Log viewer available in frontend sidebar

### Deployment
- Designed for Render.com deployment
- Uses combined FastAPI + Streamlit architecture
- Docker-based with health check endpoint at `/health`