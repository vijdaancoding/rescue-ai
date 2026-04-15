from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.api import auth, calls, voice, twilio_voice
from app.api import analysis as analysis_router
from app.api import dashboard_ws
from app.api import dispatches as dispatches_router
from app.api import analytics as analytics_router
from app.analysis import onnx_runner


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    # Reflect ORM models against the existing Supabase schema.
    # create_all is a no-op for tables that already exist.
    Base.metadata.create_all(bind=engine)

    # Load the 1.1 GB ONNX spam-detection model into memory ONCE so the first
    # real call doesn't pay the cold-start cost.
    onnx_runner.load()

    yield
    # ── Shutdown ───────────────────────────────────────────────────────────────
    # ONNX session and thread pool close with the process; nothing to clean up.


app = FastAPI(title="Rescue AI Backend", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(calls.router)
app.include_router(voice.router)
app.include_router(twilio_voice.router)
app.include_router(analysis_router.router)   # POST /api/analysis/{call_id}
app.include_router(dashboard_ws.router)      # WS  /ws/dashboard
app.include_router(dispatches_router.router) # POST/GET/PATCH /api/dispatches
app.include_router(analytics_router.router)  # GET /api/analytics/*


@app.get("/")
def root():
    return {"message": "Rescue AI Backend is running."}
