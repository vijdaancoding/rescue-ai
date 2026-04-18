"""
Global pytest configuration and shared fixtures.

This file provides:
- Test database session and models
- Mock repositories and services
- Test user and call data
- FastAPI test client
- Mock external API clients
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.models import User, CallSession, AiMetadata, Dispatch, Geolocation, AuditLog
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.api.deps import get_db, get_user_repo
from app.repositories.users import SqlUserRepository
from app.repositories.calls import SqlCallRepository
from app.repositories.dispatches import SqlDispatchRepository
from app.repositories.ai_metadata import SqlAiMetadataRepository
from app.repositories.geolocation import SqlGeolocationRepository


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE SETUP
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """
    Create an in-memory SQLite database for testing.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Automatically rollback after each test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ──────────────────────────────────────────────────────────────────────────────
# FASTAPI TEST CLIENT
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client(db_session):
    """
    FastAPI test client with mocked database dependency.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# TEST DATA FACTORIES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user in the database."""
    user = User(
        id=uuid.uuid4(),
        username="testdispatcher",
        password_hash=get_password_hash("testpassword123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_inactive(db_session: Session) -> User:
    """Create an inactive test user."""
    user = User(
        id=uuid.uuid4(),
        username="inactivedispatcher",
        password_hash=get_password_hash("testpassword123"),
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_call(db_session: Session) -> CallSession:
    """Create a test call session."""
    call = CallSession(
        id=uuid.uuid4(),
        caller_hash="hash_test_123",
        start_time=datetime.now(timezone.utc),
        status="Active",
        caller_phone="+923001234567",
        caller_city="Karachi",
        caller_state="Sindh",
        caller_country="Pakistan",
        caller_zip="75500",
        room_name="room_test_123",
    )
    db_session.add(call)
    db_session.commit()
    db_session.refresh(call)
    return call


@pytest.fixture
def test_call_incoming(db_session: Session) -> CallSession:
    """Create an incoming call session."""
    call = CallSession(
        id=uuid.uuid4(),
        caller_hash="hash_incoming_456",
        start_time=datetime.now(timezone.utc),
        status="Incoming",
        caller_phone="+923009876543",
        room_name="room_incoming_456",
    )
    db_session.add(call)
    db_session.commit()
    db_session.refresh(call)
    return call


@pytest.fixture
def test_ai_metadata(db_session: Session, test_call: CallSession) -> AiMetadata:
    """Create AI metadata for a call."""
    metadata = AiMetadata(
        analysis_id=uuid.uuid4(),
        call_id=test_call.id,
        transcript_urdu="یہ ایک ٹیسٹ ہے",
        scam_probability=45,
        sentiment_label="not_spam",
        urgency_level="medium",
        processing_latency=0.523,
        detected_keywords={"keywords": ["emergency", "help"], "word_count": 50},
    )
    db_session.add(metadata)
    db_session.commit()
    db_session.refresh(metadata)
    return metadata


@pytest.fixture
def test_dispatch(db_session: Session, test_call: CallSession) -> Dispatch:
    """Create a dispatch record."""
    dispatch = Dispatch(
        id=uuid.uuid4(),
        call_id=test_call.id,
        dispatch_type="ambulance",
        status="dispatched",
        notes="Test dispatch",
        ai_recommended=True,
    )
    db_session.add(dispatch)
    db_session.commit()
    db_session.refresh(dispatch)
    return dispatch


@pytest.fixture
def test_geolocation(db_session: Session, test_call: CallSession) -> Geolocation:
    """Create a geolocation record."""
    geo = Geolocation(
        id=1,
        call_id=test_call.id,
        latitude=24.8607,
        longitude=67.0011,
        is_simulated=False,
    )
    db_session.add(geo)
    db_session.commit()
    db_session.refresh(geo)
    return geo


# ──────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION FIXTURES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def access_token(test_user: User) -> str:
    """Generate a valid JWT access token for test user."""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(access_token: str) -> dict:
    """Return authorization headers with valid token."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def invalid_auth_headers() -> dict:
    """Return authorization headers with invalid token."""
    return {"Authorization": "Bearer invalid.token.here"}


# ──────────────────────────────────────────────────────────────────────────────
# REPOSITORY FIXTURES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def user_repo(db_session: Session) -> SqlUserRepository:
    """Create a user repository instance."""
    return SqlUserRepository(db_session)


@pytest.fixture
def call_repo(db_session: Session) -> SqlCallRepository:
    """Create a call repository instance."""
    return SqlCallRepository(db_session)


@pytest.fixture
def dispatch_repo(db_session: Session) -> SqlDispatchRepository:
    """Create a dispatch repository instance."""
    return SqlDispatchRepository(db_session)


@pytest.fixture
def ai_metadata_repo(db_session: Session) -> SqlAiMetadataRepository:
    """Create an AI metadata repository instance."""
    return SqlAiMetadataRepository(db_session)


@pytest.fixture
def geolocation_repo(db_session: Session) -> SqlGeolocationRepository:
    """Create a geolocation repository instance."""
    return SqlGeolocationRepository(db_session)


# ──────────────────────────────────────────────────────────────────────────────
# MOCK EXTERNAL SERVICES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls."""
    return AsyncMock()


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client."""
    client = MagicMock()
    client.messages.create = MagicMock()
    client.calls.stream = MagicMock()
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def mock_gemini_client():
    """Mock Google Gemini client."""
    client = AsyncMock()
    client.models.generate_content = AsyncMock()
    return client


@pytest.fixture
def mock_livekit_agent():
    """Mock LiveKit agent."""
    agent = AsyncMock()
    agent.connect = AsyncMock()
    agent.disconnect = AsyncMock()
    agent.say = AsyncMock()
    agent.process_audio = AsyncMock()
    return agent


# ──────────────────────────────────────────────────────────────────────────────
# ANALYSIS PIPELINE MOCKS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_onnx_runner():
    """Mock ONNX model runner."""
    with patch("app.analysis.onnx_runner.load") as mock_load, \
         patch("app.analysis.onnx_runner.predict", new_callable=AsyncMock) as mock_predict:
        mock_load.return_value = None
        mock_predict.return_value = {"spam_score": 0.35, "spam_label": "not_spam"}
        yield {"load": mock_load, "run": mock_predict}


@pytest.fixture
def mock_gemini_analyzer():
    """Mock Gemini analyzer."""
    with patch("app.analysis.gemini_analyzer.analyze") as mock_analyze:
        mock_analyze.return_value = {
            "urgency": "medium",
            "dispatch_types": ["ambulance"],
            "reasoning": "Test analysis",
        }
        yield mock_analyze


# ──────────────────────────────────────────────────────────────────────────────
# VOICE AGENT MOCKS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_livekit_room():
    """Mock LiveKit room connection."""
    room = AsyncMock()
    room.connect = AsyncMock()
    room.disconnect = AsyncMock()
    room.publish_data = AsyncMock()
    room.local_participant = MagicMock()
    room.local_participant.publish_track = AsyncMock()
    return room


@pytest.fixture
def mock_voice_agent_context():
    """Mock voice agent context data."""
    return {
        "call_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "room_name": "test_room_123",
        "caller_phone": "+923001234567",
        "caller_city": "Karachi",
    }


# ──────────────────────────────────────────────────────────────────────────────
# CONTEXT AND UTILITIES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_request_context():
    """Mock request context for logging."""
    context = MagicMock()
    context.trace_id = str(uuid.uuid4())
    context.user_id = str(uuid.uuid4())
    return context
