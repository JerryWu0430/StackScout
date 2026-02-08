from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import repos, tools
from routers.voice import router as voice_router, demos_router
from routers.booking import router as booking_router
from routers.twilio_webhooks import router as twilio_router
from routers.discovery import router as discovery_router
from routers.email_drafts import router as email_drafts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if os.getenv("DISCOVERY_SYNC_ENABLED", "").lower() == "true":
        from services.discovery import schedule_daily_sync
        hour = int(os.getenv("DISCOVERY_SYNC_HOUR", "3"))
        schedule_daily_sync(hour=hour)
    yield
    # Shutdown
    from services.discovery.sync import stop_scheduler
    stop_scheduler()


app = FastAPI(title="StackScout API", lifespan=lifespan)

app.include_router(tools.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# StackScout routes
app.include_router(repos.router, prefix="/api")
app.include_router(voice_router)
app.include_router(demos_router)

# CallPilot routes
app.include_router(booking_router)
app.include_router(twilio_router)

# Discovery routes
app.include_router(discovery_router)

# Email drafts routes
app.include_router(email_drafts_router)


@app.get("/")
def root():
    return {"message": "StackScout API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
