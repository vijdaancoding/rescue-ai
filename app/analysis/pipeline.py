"""
Parallel analysis pipeline.

Fires ONNX spam detection and Gemini urgency/spam analysis concurrently via
asyncio.gather(), then persists the merged result as a new row in the Supabase
ai_metadata table and broadcasts it to all dashboard WebSocket subscribers.

Called as a FastAPI BackgroundTask — creates its own DB session.
"""
import asyncio
import logging
import time
import uuid

from app.analysis import gemini_analyzer, onnx_runner
from app.db.database import SessionLocal
from app.db.models import AiMetadata, CallSession

logger = logging.getLogger(__name__)


async def run(call_id: str, transcript: str, ws_manager) -> None:
    """
    Entry point called by the /api/analysis/{call_id} background task.

    Both agents run in parallel. If one fails its result falls back to safe
    defaults — the other's result is still saved and broadcast.
    """
    t_start = time.monotonic()

    # ── 1. Run both agents in parallel ────────────────────────────────────────
    onnx_result, gemini_result = await asyncio.gather(
        onnx_runner.predict(transcript),
        gemini_analyzer.analyze(transcript),
        return_exceptions=True,
    )

    processing_latency = round(time.monotonic() - t_start, 3)

    if isinstance(onnx_result, Exception):
        logger.warning("ONNX inference failed for call %s: %s", call_id, onnx_result)
        onnx_result = {"spam_label": "not_spam", "spam_score": 0.0}

    if isinstance(gemini_result, Exception):
        logger.warning("Gemini analysis failed for call %s: %s", call_id, gemini_result)
        gemini_result = {
            "spam_score": 0.0,
            "spam_label": "not_spam",
            "urgency_score": 0.5,
            "urgency_label": "medium",
            "reasoning": "Analysis unavailable.",
            "dispatch_recommendation": [],
        }

    # ── 2. Merge results ───────────────────────────────────────────────────────
    # Average both spam scores for a more robust signal
    combined_spam_score = round(
        (onnx_result["spam_score"] + gemini_result.get("spam_score", 0.0)) / 2, 4
    )
    combined_spam_label = "spam" if combined_spam_score >= 0.5 else "not_spam"
    urgency_label = gemini_result.get("urgency_label", "medium")
    urgency_score = gemini_result.get("urgency_score", 0.5)

    # scam_probability stored as 0–100 integer (Supabase column is bigint)
    scam_probability_int = round(combined_spam_score * 100)

    # ── 3. Persist to ai_metadata table (own session) ─────────────────────────
    analysis_count = 0
    db = SessionLocal()
    try:
        call_uuid = uuid.UUID(call_id)

        row = AiMetadata(
            call_id=call_uuid,
            transcript_urdu=transcript,
            scam_probability=scam_probability_int,   # bigint, 0–100
            sentiment_label=combined_spam_label,      # "spam" | "not_spam"
            urgency_level=urgency_label,              # "low" | "medium" | "high" | "critical"
            processing_latency=processing_latency,
            detected_keywords={                       # flexible JSON blob
                "onnx_spam_score": onnx_result["spam_score"],
                "gemini_spam_score": gemini_result.get("spam_score", 0.0),
                "urgency_score": urgency_score,
                "reasoning": gemini_result.get("reasoning", ""),
                "word_count": len(transcript.split()),
            },
        )
        db.add(row)
        db.flush()  # get the row into the session before counting

        # Count how many analysis rows exist for this call (for display)
        analysis_count = (
            db.query(AiMetadata)
            .filter(AiMetadata.call_id == call_uuid)
            .count()
        )
        db.commit()
    except Exception as exc:
        logger.error("DB save failed for call %s: %s", call_id, exc)
        db.rollback()
    finally:
        db.close()

    # ── 4. Build broadcast payload ─────────────────────────────────────────────
    payload = {
        "type": "analysis_update",
        "call_id": call_id,
        # Combined spam signal (0.0–1.0)
        "spam_score": combined_spam_score,
        "spam_label": combined_spam_label,
        # Individual model scores for transparency
        "onnx_spam_score": onnx_result["spam_score"],
        "gemini_spam_score": gemini_result.get("spam_score", 0.0),
        # Urgency from Gemini
        "urgency_score": urgency_score,
        "urgency_label": urgency_label,
        "reasoning": gemini_result.get("reasoning", ""),
        "dispatch_recommendation": gemini_result.get("dispatch_recommendation", []),
        "transcript_word_count": len(transcript.split()),
        "processing_latency_ms": round(processing_latency * 1000),
        "analysis_count": analysis_count,
    }

    # ── 5. Push to all dashboard WebSocket subscribers ────────────────────────
    await ws_manager.broadcast(payload)
    logger.info(
        "Analysis #%d for call %s — spam=%d%% (%s) urgency=%s (%.0f%%) latency=%dms",
        analysis_count,
        call_id,
        scam_probability_int,
        combined_spam_label,
        urgency_label,
        urgency_score * 100,
        round(processing_latency * 1000),
    )


def validate_input(transcript: str) -> bool:
    """Return True if transcript is non-empty, False otherwise."""
    return bool(transcript and transcript.strip())


async def run_analysis(transcript: str, call_id: str) -> dict | None:
    """
    Simplified entry point for tests — runs both models without DB persistence
    or WebSocket broadcast.
    """
    if not validate_input(transcript):
        return None

    onnx_result, gemini_result = await asyncio.gather(
        onnx_runner.predict(transcript),
        gemini_analyzer.analyze(transcript),
        return_exceptions=True,
    )

    if isinstance(onnx_result, Exception) and isinstance(gemini_result, Exception):
        return None

    if isinstance(onnx_result, Exception):
        onnx_result = {"spam_score": 0.0, "spam_label": "not_spam"}
    if isinstance(gemini_result, Exception):
        gemini_result = {"spam_score": 0.0, "spam_label": "not_spam", "urgency_label": "medium"}

    combined_spam_score = round(
        (onnx_result["spam_score"] + gemini_result.get("spam_score", 0.0)) / 2, 4
    )
    return {
        "spam_score": round(combined_spam_score * 100),
        "spam_label": "spam" if combined_spam_score >= 0.5 else "not_spam",
        "urgency_label": gemini_result.get("urgency_label", "medium"),
    }
