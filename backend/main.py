from fastapi import FastAPI

from .routers import amendments, norms, proposals, tasks

app = FastAPI()


app.include_router(amendments.router)
app.include_router(norms.router)
app.include_router(proposals.router)
app.include_router(tasks.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}