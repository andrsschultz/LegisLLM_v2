# LegisLLM Frontend (Next.js)

This is the Next.js frontend for the LegisLLM application, providing a modern web interface for AI-assisted legal drafting.

## Features

- **5-Step Wizard Workflow**: Task Description → Context Identification → Proposal Development → Evaluation → Finalization
- **Multi-Provider AI Support**: Works with OpenAI and DeepInfra models
- **Session State Management**: Preserves data across tabs and workflow steps
- **Real-time Logging**: Debug and API call logging with export functionality
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **TypeScript**: Full type safety and excellent developer experience

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your configuration:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
src/
├── app/                 # Next.js App Router
├── components/          # React components
│   ├── tabs/           # Workflow step components
│   ├── Layout.tsx      # Main layout wrapper
│   ├── ModelSelector.tsx
│   └── LogViewer.tsx
├── contexts/           # React Context providers
│   └── AppContext.tsx  # Global state management
├── lib/               # Utility libraries
│   └── api.ts         # API client
└── types/             # TypeScript type definitions
    └── index.ts
```

## API Configuration

The frontend communicates with the FastAPI backend through environment variables:

- `NEXT_PUBLIC_BACKEND_URL`: Backend API base URL (default: http://localhost:8000)

API keys are stored in browser localStorage:
- `openai_api_key`: OpenAI API key
- `deepinfra_api_key`: DeepInfra API key

## Development

### Available Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Key Components

1. **AppContext**: Global state management using React Context and useReducer
2. **Layout**: Main application layout with navigation and sidebar
3. **Tab Components**: Individual workflow steps (TaskDescription, ContextIdentification, etc.)
4. **ModelSelector**: AI model selection and API key management
5. **LogViewer**: Debug logging and API call monitoring

## Deployment

### Production Build

```bash
npm run build
npm start
```

### Docker Deployment

The application can be deployed using Docker. See the main project README for deployment instructions.

### Environment Variables for Production

```env
NEXT_PUBLIC_BACKEND_URL=https://your-api-domain.com
```

## Workflow Steps

1. **Task Description**: Enter legislative task requirements
2. **Context Identification**: AI identifies relevant legal norms
3. **Proposal Development**: Generate abstract regulatory alternatives  
4. **Evaluation**: Legal and technical assessment of proposals
5. **Finalization**: Generate final amendment text

## API Integration

The frontend integrates with these backend endpoints:

- `GET /models` - Available AI models
- `POST /identify` - Identify relevant legal norms
- `POST /identify_multistep` - Multi-step norm identification
- `POST /generate_proposals` - Generate amendment proposals
- `POST /evaluate_proposals` - Evaluate proposals
- `POST /deep_evaluate_proposals` - Deep evaluation
- `POST /amend` - Generate final amendment text

## State Management

The application uses React Context for state management with the following structure:

```typescript
interface AppState {
  taskDescription: string;
  selectedModel: string;
  relevantNorms: NormEntry[] | null;
  amendmentProposals: ProposalEntry[] | null;
  evaluatedProposals: EvaluatedProposal[] | null;
  finalAmendment: string | null;
  currentTab: number;
  multistepReasoning: boolean;
  logs: string[];
}
```

## Contributing

1. Follow TypeScript best practices
2. Use meaningful component and variable names
3. Maintain consistent styling with Tailwind CSS
4. Add proper error handling for API calls
5. Test thoroughly across different browsers