import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Boolean

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
    caller_hash = Column(String, nullable=False) # Privacy requirement
    start_time = Column(DateTime, default=get_utc_now)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="Incoming") # Incoming, Active, Dispatched, FalseAlarm
    audio_path_encrypted = Column(String, nullable=True)