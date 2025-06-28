# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
- **Backend**: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- **Frontend**: `cd frontend && npm run dev`
- **Full development setup**:
  ```bash
  # Terminal 1 - Backend
  uvicorn backend.main:app --host 0.0.0.0 --port 8000
  
  # Terminal 2 - Frontend  
  cd frontend && npm run dev
  ```

### Dependencies
- **Backend**: `pip install -r requirements.txt`
- **Frontend**: `cd frontend && npm install`

### Frontend Development
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`
- **Start production**: `cd frontend && npm start`

### Docker Operations
- **Build**: `docker build -t legisllm .`
- **Run**: `docker run -p 8501:8501 legisllm`

## Architecture Overview

LegisLLM is a German legal AI application with a **dual-architecture** design for legislative amendment drafting:

### Backend (FastAPI)
- **Location**: `/backend/`
- **Entry point**: `backend/main.py`
- **Core modules**:
  - `core/domain_logic.py` - Main AI logic for legal norm analysis and multi-step reasoning
  - `core/llm_service.py` - LLM provider integration (OpenAI, DeepInfra)
  - `core/xml_parser.py` - German legal XML document parsing with structured section extraction
  - `core/models.py` - Pydantic data models for API requests/responses
  - `core/config.py` - Model configuration and enums with provider detection
  - `core/auth.py` - API key authentication

### Frontend (Next.js + TypeScript)
- **Location**: `/frontend/src/`
- **Architecture**: Context-driven 5-step wizard interface
- **Key components**:
  - `contexts/AppContext.tsx` - Global state management with AppState interface
  - `components/tabs/` - Step-specific UI components
  - `lib/api.ts` - Backend API integration
  - `types/index.ts` - TypeScript interfaces matching backend models

### API Endpoints
The backend provides these main endpoints:
- `/identify` - Single-step legal norm identification
- `/identify_multistep` - Multi-step reasoning for complex norm identification
- `/generate_proposals` - Generate amendment proposals based on identified norms
- `/evaluate_proposals` - Evaluate proposals against legal criteria
- `/deep_evaluate_proposals` - Detailed evaluation with juristic analysis
- `/amend` - Generate final amendment text

### Data Layer
- **Legal documents**: Stored as XML files in `/backend/data/`
- **Supported laws**: German tax law (EStG, UStG, GewStG, AO, etc.)
- **Format**: Structured XML with `jurabk`, `enbez`, and `P` elements for law identification

## Key Design Patterns

### AI Provider Abstraction
- Models configured in `core/config.py` with `ModelEnum`
- Provider detection via `is_deepinfra_model()` function
- Supports OpenAI (GPT models) and DeepInfra (Llama, DeepSeek) models
- API keys managed through environment variables

### Multi-step AI Reasoning
- Standard and multistep reasoning modes available via separate endpoints
- Multistep mode breaks complex legal analysis into sub-tasks
- Reasoning models (o1, o3, DeepSeek-R1) specifically support multistep workflows

### State Management Architecture
- Frontend uses React Context (`AppContext`) for global state
- `AppState` interface defines complete application state structure
- Each workflow step (0-4) stores results for subsequent steps
- Tab navigation with persistent state across workflow

### Legal Document Processing
- XML parsing handles German legal document structure
- `extract_section_from_law()` retrieves specific legal provisions
- `extract_table_of_contents()` for navigation and discovery

## Environment Configuration

Required environment variables:
- `OPENAI_API_KEY` - For OpenAI models (GPT-3.5, GPT-4, o1, o3 series)
- `DEEPINFRA_API_KEY` - For DeepInfra models (Llama, DeepSeek)
- `BACKEND_URL` - Frontend-to-backend communication (default: http://localhost:8000)

## Development Notes

### XML Document Structure
German legal documents follow a specific XML schema:
- `jurabk` - Law abbreviation (e.g., "EStG", "UStG")
- `enbez` - Section designation (e.g., "§ 21")
- `P` - Paragraph/subsection number (e.g., "2a")

### Model Selection and Provider Detection
- Default model: GPT-3.5-turbo
- Reasoning models (o1, o3, DeepSeek-R1) automatically enable multistep capabilities
- Provider automatically detected via model string matching in `is_deepinfra_model()`

### TypeScript Integration
- Shared type definitions in `frontend/src/types/index.ts`
- Matches backend Pydantic models for type safety
- Complex nested interfaces for legal evaluation data structures

### API Authentication
- All endpoints require API key authentication via `verify_api_key()` dependency
- Keys passed as dependencies to router functions
- Supports both OpenAI and DeepInfra API keys based on model selection