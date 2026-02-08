from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import repos, tools
from routers.voice import router as voice_router, demos_router
from routers.booking import router as booking_router
from routers.twilio_webhooks import router as twilio_router

app = FastAPI(title="CallPilot API")

app.include_router(tools.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# StackScout routes (kept for compatibility)
app.include_router(repos.router, prefix="/api")
app.include_router(voice_router)
app.include_router(demos_router)

# CallPilot routes
app.include_router(booking_router)
app.include_router(twilio_router)


@app.get("/")
def root():
    return {"message": "CallPilot API - AI Appointment Scheduling"}


@app.get("/health")
def health():
    return {"status": "ok"}
