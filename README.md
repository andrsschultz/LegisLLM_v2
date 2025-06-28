# LegisLLM

LegisLLM provides AI driven assistance for drafting legislative amendments.

## Architecture

- **Backend**: FastAPI
- **Frontend**: Next.js 

## How to Run

### Quick Start
```bash
./run.sh
```

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

2. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY="your-key"
   export DEEPINFRA_API_KEY="your-key"
   export BACKEND_URL="http://localhost:8000"
   ```

3. **Run backend**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

4. **Run frontend**:
   ```bash
   cd frontend && npm run dev
   ```

### Docker
```bash
docker build -t legisllm .
docker run -p 8501:8501 legisllm
```

## API Endpoints

- `/identify` - Legal norm identification
- `/identify_multistep` - Multi-step reasoning
- `/generate_proposals` - Amendment proposals
- `/evaluate_proposals` - Proposal evaluation
- `/amend` - Final amendment generation

