from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.analysis import onnx_runner
from app.api import auth, calls, voice, twilio_voice, location_endpoint
from app.api import analysis as analysis_router
from app.api import analytics as analytics_router
from app.api import dashboard_ws
from app.api import dispatches as dispatches_router
from app.api import health as health_router
from app.api import settings as settings_router
from app.api.errors import install_error_handlers
from app.core import http_client
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    configure_logging()
    logger.info("Starting {}", settings.PROJECT_NAME)

    # Reflect ORM models against the existing Supabase schema. `create_all`
    # is a no-op for tables that already exist.
    Base.metadata.create_all(bind=engine)

    # Warm the shared HTTP client and the 1.1 GB ONNX spam model so the first
    # real call doesn't eat the cold-start cost.
    await http_client.startup()
    onnx_runner.load()
    logger.info("Startup complete")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    await http_client.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(title="Rescue AI Backend", version="1.0", lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_origin_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

install_error_handlers(app)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(calls.router)
app.include_router(voice.router)
app.include_router(twilio_voice.router)
app.include_router(location_endpoint.router)
app.include_router(analysis_router.router)    # POST /api/analysis/{call_id}
app.include_router(dashboard_ws.router)       # WS  /ws/dashboard
app.include_router(dispatches_router.router)  # POST/GET/PATCH /api/dispatches
app.include_router(analytics_router.router)   # GET /api/analytics/*
app.include_router(health_router.router)      # /health/* + WS /health/ws
app.include_router(settings_router.router)    # GET/PUT /api/settings


@app.get("/")
def root():
    return {"message": "Rescue AI Backend is running."}
