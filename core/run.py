import os
import base64
import asyncio
from dotenv import load_dotenv
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.util.types import AttributeValue
from livekit import agents, api
from livekit.agents import AgentSession, RoomInputOptions, WorkerOptions, metrics
from livekit.plugins import noise_cancellation, silero, deepgram, google, openai
from livekit.agents.voice import MetricsCollectedEvent
from livekit.agents.telemetry import set_tracer_provider

from rescue_agent import EmergencyAgent
from tts import TTS

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLIFTAI_API_KEY = os.getenv("UPLIFTAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

room_name = "rescue_ai"
agent_name = "emergency_agent"

tts = TTS( 
    api_key=UPLIFTAI_API_KEY,
    voice_id="v_30s70t3a",
    output_format="MP3_22050_32",
)


async def list_participants(room_name: str):
    lkapi = api.LiveKitAPI()  # uses LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET envs
    try:
        parts = await lkapi.room.list_participants(api.ListParticipantsRequest(room=room_name))
    except Exception as e:
        print("error listing participants:", e)
        await lkapi.aclose()
        return
    print("\n\nParticipants in", room_name)
    for p in parts.participants:
        tracks = [(t.sid, t.type, t.source) for t in (p.tracks or [])]
        print(" - identity:", p.identity, "sid:", p.sid, "tracks:", tracks, "metadata:", p.metadata)
    await lkapi.aclose()

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        preemptive_generation=True,
        stt=openai.STT(model="gpt-4o-transcribe"),
        llm=openai.LLM(model="gpt-4o-mini", api_key=OPENAI_API_KEY),
        tts=tts,
        vad=silero.VAD.load(),
    )

    print(f"\n\n\nDEBUG :{ctx.room}, {ctx.job} \n\n")

    await session.start(
        room=ctx.room,
        agent=EmergencyAgent(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":

    #asyncio.run(delete_all_dispatches(room_name))  
    #asyncio.run(create_explicit_dispatch())
    asyncio.run(list_participants("rescue_ai"))
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

