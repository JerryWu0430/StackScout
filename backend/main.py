from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import repos, tools
from routers.voice import router as voice_router, demos_router

app = FastAPI(title="StackScout API")

app.include_router(tools.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router, prefix="/api")
app.include_router(voice_router)
app.include_router(demos_router)


@app.get("/")
def root():
    return {"message": "StackScout API"}


@app.get("/health")
def health():
    return {"status": "ok"}
