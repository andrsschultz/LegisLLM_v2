from fastapi import FastAPI

from .routers import amend, evaluate, norms, proposals

app = FastAPI()


app.include_router(amend.router)
app.include_router(norms.router)
app.include_router(proposals.router)
app.include_router(evaluate.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}