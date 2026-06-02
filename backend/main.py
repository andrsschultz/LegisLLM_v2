from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import amend, evaluate, gesetzesentwurf, getModels, norms, proposals, stream

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:3001",  # Local development alternate port
        "http://127.0.0.1:3000",  # Local development via loopback IP
        "http://127.0.0.1:3001",  # Local development alternate port via loopback IP
        "https://legisllm.onrender.com",  # Frontend domain
        "https://legisllm-frontend.onrender.com",  # Alternative frontend domain
        "https://www.legisllm.de",  # Main domain
        "https://legisllm.de"  # Domain without www
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(amend.router)
app.include_router(gesetzesentwurf.router)
app.include_router(norms.router)
app.include_router(proposals.router)
app.include_router(evaluate.router)
app.include_router(getModels.router)
app.include_router(stream.router)


@app.get("/")
async def root():
    return {"message": "This is the LegisLLM backend API. Use the endpoints to interact with the service. Documentation: https://api.legisllm.de/docs ;  Frontend: https://www.legisllm.de"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
