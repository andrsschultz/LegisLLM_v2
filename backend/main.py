from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import amend, evaluate, getModels, norms, proposals

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://legisllm.onrender.com",  # Frontend domain
        "https://legisllm-frontend.onrender.com",  # Alternative frontend domain
        "https://www.legisllm.de/"
        "https://legisllm.de/"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(amend.router)
app.include_router(norms.router)
app.include_router(proposals.router)
app.include_router(evaluate.router)
app.include_router(getModels.router)


@app.get("/")
async def root():
    return {"message": "This is the LegisLLM backend API. Use the endpoints to interact with the service. Documentation: https://legisllm-full-stack.onrender.com/docs ;  Frontend: https://legisllm.onrender.com"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}