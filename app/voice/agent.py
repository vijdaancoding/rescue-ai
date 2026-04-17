from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import logging
import os
import time
from typing import AsyncGenerator

import httpx
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, WorkerType, inference, TurnHandlingOptions
from livekit.agents.voice.room_io import RoomOptions
from livekit.plugins import upliftai, silero, groq
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger(__name__)

AGENT_NAME = "rescue-operator"

# URL of the FastAPI backend — agent posts transcripts here for analysis.
_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Per-call analysis throttle settings
_MIN_WORDS = 20
_COOLDOWN_SEC = 8

# ── Pre-synthesized greeting cache ─────────────────────────────────────────────
# Synthesized once at the first call handled by this worker process.
# Subsequent calls reuse cached frames — no TTS round-trip for the greeting.
_GREETING_TEXT = "ریسکیو ہیلپ لائن، میں آپ کی کس طرح مدد کر سکتی ہوں؟"
_GREETING_FRAMES: list[rtc.AudioFrame] = []
_greeting_lock = asyncio.Lock()


async def _preload_greeting(tts_instance: upliftai.TTS) -> None:
    """Synthesize the greeting once and store audio frames for reuse."""
    global _GREETING_FRAMES
    async with _greeting_lock:
        if _GREETING_FRAMES:
            return  # already cached by a prior call
        frames: list[rtc.AudioFrame] = []
        async for event in tts_instance.synthesize(_GREETING_TEXT):
            frames.append(event.frame)
        _GREETING_FRAMES = frames
        logger.info("Greeting pre-synthesized: %d frames cached", len(frames))


_BASE_INSTRUCTIONS = """
# ریسکیو ہیلپ لائن آپریٹر

## بنیادی شناخت
آپ ریسکیو ایمرجنسی ہیلپ لائن (1122 / 911) کی خاتون آپریٹر ہیں۔ آپ کا کام لوگوں کی پریشانی میں مدد کرنا اور صحیح ایمرجنسی سروس کو بھیجنا ہے۔

## زبان کے اصول
- صرف پاکستانی اردو استعمال کریں — نہ رومن اردو، نہ انگریزی
- مونث گرامر (میں سمجھتی ہوں، بتاتی ہوں، پوچھتی ہوں)
- کالر کے لیے احترامی انداز (آپ، جناب، صاحب/صاحبہ)
- سادہ اور واضح زبان جو ہر کوئی سمجھ سکے
- پرسکون اور اطمینان بخش لہجہ

## پہلا جواب
فوری طور پر کہیں: "ریسکیو ہیلپ لائن، میں آپ کی کس طرح مدد کر سکتی ہوں؟"

## بات چیت کا طریقہ
- مختصر، واضح سوالات پوچھیں
- ایک وقت میں ایک ہی سوال کریں
- صورتحال: کیا ہوا؟ کہاں ہوا؟ کتنے لوگ متاثر ہیں؟
- ایمرجنسی کی قسم معلوم کریں: آگ، حادثہ، طبی ضرورت، امن و امان
{location_instructions}
- متاثرہ شخص کی حالت پوچھیں

## ایمرجنسی کی اقسام
- آگ ← فائر بریگیڈ بھیجنا
- حادثہ / زخمی ← ریسکیو ٹیم اور ایمبولینس
- طبی ضرورت ← ایمبولینس (1122)
- جرم / امن و امان ← پولیس (15)

## جواب دینے کا انداز
- بغیر علامات اور بُلٹ پوائنٹس کے بولیں
- دو سے تین جملوں میں بات ختم کریں
- گھبراہٹ میں ہو تو تسلی دیں: "فکر نہ کریں، مدد آ رہی ہے"
"""

_LOCATION_UNKNOWN = "- پتہ اور قریبی نشان دہی لازمی لیں"

_LOCATION_KNOWN_TEMPLATE = """
## مقام کی معلومات (GPS سے پہلے سے دستیاب)
کالر کا مقام پہلے سے معلوم ہے: {location_label}
آپ کو مقام دوبارہ نہیں پوچھنا چاہیے۔ صرف مختصر تصدیق کریں:
"آپ {location_label} میں ہیں، کیا یہ درست ہے؟"
اگر کالر نے تصدیق کی تو فوری ایمرجنسی کی تفصیل پوچھیں۔
اگر کالر نے غلط بتایا تو صحیح پتہ لیں۔
""".strip()


def _build_instructions(location_context: dict | None) -> str:
    if location_context and location_context.get("has_location"):
        city = location_context.get("city")
        state = location_context.get("state")
        lat = location_context.get("lat")
        lng = location_context.get("lng")

        if city and state:
            label = f"{city}، {state}"
        elif city:
            label = city
        elif lat is not None and lng is not None:
            label = f"{lat:.4f}, {lng:.4f}"
        else:
            label = None

        if label:
            location_block = _LOCATION_KNOWN_TEMPLATE.format(location_label=label)
            return _BASE_INSTRUCTIONS.format(location_instructions=location_block)

    return _BASE_INSTRUCTIONS.format(location_instructions=_LOCATION_UNKNOWN)


async def _fetch_call_context(room_name: str) -> dict:
    """Fetch pre-known call context (location) from the backend at agent startup."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{_BACKEND_URL}/calls/context/{room_name}")
            if r.status_code == 200:
                return r.json()
    except Exception as exc:
        logger.warning("Could not fetch call context for room %s: %s", room_name, exc)
    return {"has_location": False}


class Assistant(Agent):
    """
    Rescue helpline operator (Urdu-speaking, female).

    Per-turn transcript accumulation triggers fire-and-forget analysis via
    the FastAPI analysis pipeline (ONNX + Gemini in parallel).
    """

    def __init__(self, call_id: str, location_context: dict | None = None) -> None:
        self._call_id = call_id
        self._transcript_parts: list[str] = []
        self._last_analysis_at: float = 0.0
        self._first_user_turn_analyzed: bool = False

        super().__init__(instructions=_build_instructions(location_context))

    # ── Transcript hook ────────────────────────────────────────────────────────

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        """Accumulate caller transcript and trigger analysis off the voice path."""
        content = getattr(new_message, "content", "") or ""
        if isinstance(content, list):
            text = " ".join(str(c) for c in content if c).strip()
        else:
            text = str(content).strip()

        if not text:
            return

        self._transcript_parts.append(text)

        if not self._first_user_turn_analyzed:
            # Fire immediately on the caller's first real turn regardless of word
            # count — gives the dashboard an early spam/urgency signal before the
            # 20-word threshold is reached. The AI's preemptive greeting is spoken
            # by the agent, not the caller, so it never reaches this hook.
            self._first_user_turn_analyzed = True
            self._last_analysis_at = time.monotonic()  # start cooldown from here
            asyncio.create_task(self._post_analysis())
        else:
            asyncio.create_task(self._maybe_post_analysis())

    async def _post_analysis(self) -> None:
        """POST current transcript unconditionally (used for first-turn early signal)."""
        full_transcript = " ".join(self._transcript_parts)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{_BACKEND_URL}/api/analysis/{self._call_id}",
                    json={"transcript": full_transcript},
                )
        except Exception as exc:
            logger.warning("Failed to post early analysis for call %s: %s", self._call_id, exc)

    async def _maybe_post_analysis(self) -> None:
        """POST accumulated transcript once ≥20 words and cooldown has elapsed."""
        full_transcript = " ".join(self._transcript_parts)
        word_count = len(full_transcript.split())
        now = time.monotonic()

        if word_count < _MIN_WORDS:
            return
        if (now - self._last_analysis_at) < _COOLDOWN_SEC:
            return

        self._last_analysis_at = now

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{_BACKEND_URL}/api/analysis/{self._call_id}",
                    json={"transcript": full_transcript},
                )
        except Exception as exc:
            logger.warning("Failed to post analysis for call %s: %s", self._call_id, exc)


# ── Entrypoint ─────────────────────────────────────────────────────────────────

async def entrypoint(ctx: agents.JobContext):
    meta: dict = {}
    if ctx.job.metadata:
        try:
            meta = json.loads(ctx.job.metadata)
        except json.JSONDecodeError:
            pass

    caller_identity: str | None = meta.get("caller_identity")
    call_id: str = meta.get("call_id", "")

    await ctx.connect()

    # Fetch pre-known location context for this room (set by GPS before the call).
    # Falls back gracefully if the endpoint is unreachable or returns nothing.
    location_context = await _fetch_call_context(ctx.room.name)

    tts = upliftai.TTS(
        voice_id="v_meklc281",
        output_format="MP3_22050_32",
    )

    # Pre-synthesize greeting on first call; cached frames reused on all subsequent
    # calls handled by this worker — eliminates TTS latency for the opening phrase.
    await _preload_greeting(tts)

    # v1.5 consolidated all turn/interruption kwargs into TurnHandlingOptions.
    # Old flat kwargs still work but emit deprecation warnings and will be
    # removed in v2.0. preemptive_generation is now default-True in v1.5.
    session = AgentSession(
        stt=groq.STT(model="whisper-large-v3-turbo", language="ur"),
        llm=inference.LLM(model="google/gemini-2.5-flash"),
        tts=tts,
        vad=silero.VAD.load(),
        turn_handling=TurnHandlingOptions(
            # Context-aware turn detection: Qwen2.5-0.5B reads the transcript and
            # predicts end-of-thought, not silence alone. Hindi weights (99.4% TP)
            # are the closest language to Urdu in the multilingual model.
            turn_detection=MultilingualModel(),
            endpointing={
                # Dynamic endpointing adapts the delay within [min_delay, max_delay]
                # based on the caller's cadence — snappier for fast speakers, more
                # patient for slow ones. Well-suited to high-variance emergency calls.
                "mode": "dynamic",
                "min_delay": 0.3,
                "max_delay": 1.5,
            },
            interruption={
                # Adaptive interruption handling (v1.5): audio-based ML classifier
                # rejects coughs/sighs/backchannels as false interruptions. 86%
                # precision at 500ms overlap; 64% faster than VAD alone.
                "mode": "adaptive",
                "min_duration": 0.4,
                "min_words": 2,
                "resume_false_interruption": True,
                "false_interruption_timeout": 1.5,
            },
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(call_id=call_id, location_context=location_context),
        room_options=RoomOptions(participant_identity=caller_identity),
    )

    # Play the pre-synthesized greeting from cached frames.
    # No TTS network call needed — audio streams directly from memory.
    async def _cached_greeting() -> AsyncGenerator[rtc.AudioFrame, None]:
        for frame in _GREETING_FRAMES:
            yield frame

    await session.say(
        _GREETING_TEXT,
        audio=_cached_greeting(),
        allow_interruptions=False,
    )


if __name__ == "__main__":
    agent_port = int(os.getenv("AGENT_PORT", "8082"))
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name=AGENT_NAME,
        worker_type=WorkerType.ROOM,
        initialize_process_timeout=60,
        port=agent_port,
    ))
