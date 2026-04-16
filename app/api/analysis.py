"""
Internal endpoint called by the LiveKit agent worker to submit a transcript
for parallel analysis.

Returns 202 immediately — the actual ONNX + Gemini work runs as a
BackgroundTask so the agent is never blocked waiting for inference results.

Note: This endpoint is intentionally unprotected (internal service call from
the agent worker on the same host). Add an internal API key header if you
expose this beyond localhost in production.
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.analysis import pipeline
from app.api.dashboard_ws import manager

router = APIRouter(prefix="/api", tags=["Analysis"])


class AnalysisRequest(BaseModel):
    transcript: str


@router.post("/analysis/{call_id}", status_code=202)
async def trigger_analysis(
    call_id: str,
    body: AnalysisRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Queue parallel ONNX + Gemini analysis for a call transcript.
    The agent worker calls this after each caller turn.
    """
    background_tasks.add_task(pipeline.run, call_id, body.transcript, manager)
    return {"status": "queued", "call_id": call_id}
