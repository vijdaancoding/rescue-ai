import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    Column, String, DateTime, Boolean, Float, BigInteger, Text,
    ForeignKey, JSON
)

from app.db.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # Role removed as requested. Every user is a Dispatcher for now.


class CallSession(Base):
    __tablename__ = "call_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caller_hash = Column(String, nullable=False)  # Privacy requirement
    start_time = Column(DateTime, default=get_utc_now)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="Incoming")  # Incoming, Active, Dispatched, FalseAlarm
    audio_path_encrypted = Column(String, nullable=True)
    caller_phone = Column(String, nullable=True)
    caller_city = Column(String, nullable=True)
    caller_state = Column(String, nullable=True)
    caller_country = Column(String, nullable=True)
    caller_zip = Column(String, nullable=True)
    room_name = Column(String, nullable=True)

class AiMetadata(Base):
    """
    Stores AI analysis results per analysis run (one row per call snapshot).
    Linked to call_sessions via call_id.
    Maps to the existing Supabase ai_metadata table.
    """
    __tablename__ = "ai_metadata"
    analysis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"), nullable=True)
    transcript_urdu = Column(Text, nullable=True)
    # Spam/scam probability stored as integer 0–100 (bigint in Supabase)
    scam_probability = Column(BigInteger, nullable=True)
    # "spam" | "not_spam"
    sentiment_label = Column(String, nullable=True)
    # "low" | "medium" | "high" | "critical"
    urgency_level = Column(String, nullable=True)
    # Seconds taken to complete the parallel ONNX + Gemini analysis
    processing_latency = Column(Float, nullable=True)
    # JSON blob: onnx_spam_score, gemini_spam_score, reasoning, word_count
    detected_keywords = Column(JSON, nullable=True)


class Geolocation(Base):
    """Caller geolocation data (populated by Twilio webhook or future GPS feature)."""
    __tablename__ = "geolocation"
    id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_simulated = Column(Boolean, default=True)


class Dispatch(Base):
    """Emergency dispatch record — one row per service type dispatched per call."""
    __tablename__ = "dispatches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False)
    dispatch_type = Column(String, nullable=False)   # police | ambulance | firefighters
    status = Column(String, nullable=False, default="dispatched")  # dispatched | en_route | on_scene | resolved
    notes = Column(Text, nullable=True)
    ai_recommended = Column(Boolean, default=False)


class AuditLog(Base):
    """Audit trail for call-related actions."""
    __tablename__ = "audit_logs"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    action_type = Column(String, nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    description = Column(Text, nullable=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"))
