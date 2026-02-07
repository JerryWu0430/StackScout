from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import repos

app = FastAPI(title="StackScout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "StackScout API"}


@app.get("/health")
def health():
    return {"status": "ok"}
