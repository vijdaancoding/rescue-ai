"""
Internal endpoint called by the LiveKit agent worker to submit a transcript
for parallel analysis.

Returns 202 immediately — ONNX + Gemini work runs as a BackgroundTask so the
agent is never blocked waiting for inference results.

Intentionally unprotected (internal service call from the agent worker on
the same host). Add an internal API key header if you expose this beyond
localhost in production.
"""
from fastapi import APIRouter, BackgroundTasks

from app.analysis import pipeline
from app.api.dashboard_ws import manager
from app.schemas.location import AnalysisRequest

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analysis/{call_id}", status_code=202)
async def trigger_analysis(
    call_id: str,
    body: AnalysisRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    background_tasks.add_task(pipeline.run, call_id, body.transcript, manager)
    return {"status": "queued", "call_id": call_id}
