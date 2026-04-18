"""
Internal endpoint called by the LiveKit agent worker to submit a transcript
for parallel analysis.

Returns 202 immediately — ONNX + Gemini work runs as a BackgroundTask so the
agent is never blocked waiting for inference results.

Intentionally unprotected (internal service call from the agent worker on
the same host). Add an internal API key header if you expose this beyond
localhost in production.
"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.analysis import pipeline
from app.api.dashboard_ws import manager
from app.api.deps import get_ai_metadata_repo
from app.repositories.ai_metadata import AiMetadataRepository
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


@router.get("/analysis/{call_id}/latest")
def get_latest_analysis(
    call_id: str,
    ai_metadata: AiMetadataRepository = Depends(get_ai_metadata_repo),
) -> dict:
    """Return the newest analysis row for this call in the same shape the
    dashboard WebSocket broadcasts — lets observers seed their state from
    REST when they connect mid-call (and thus miss earlier broadcasts)."""
    try:
        cid = uuid.UUID(call_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid call_id")
    latest = ai_metadata.latest_for_calls([cid]).get(call_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="No analysis yet for this call")
    count = ai_metadata.count_for_call(cid)
    kw = latest.detected_keywords or {}
    spam_score = round(((latest.scam_probability or 0) / 100.0), 4)
    return {
        "type": "analysis_update",
        "call_id": call_id,
        "spam_score": spam_score,
        "spam_label": latest.sentiment_label,
        "onnx_spam_score": kw.get("onnx_spam_score", 0.0),
        "gemini_spam_score": kw.get("gemini_spam_score", 0.0),
        "urgency_score": kw.get("urgency_score", 0.5),
        "urgency_label": latest.urgency_level,
        "reasoning": kw.get("reasoning", ""),
        "dispatch_recommendation": kw.get("dispatch_recommendation", []),
        "transcript_word_count": kw.get("word_count", 0),
        "processing_latency_ms": round((latest.processing_latency or 0) * 1000),
        "analysis_count": count,
    }
