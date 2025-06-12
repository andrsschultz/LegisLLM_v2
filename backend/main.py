from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import amend, evaluate, getModels, norms, proposals

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(amend.router)
app.include_router(norms.router)
app.include_router(proposals.router)
app.include_router(evaluate.router)
app.include_router(getModels.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}