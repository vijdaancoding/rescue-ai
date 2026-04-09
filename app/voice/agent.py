from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, inference
from livekit.plugins import (
    openai,
    upliftai,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
# Pakistan History Voice Assistant

## Core Identity
You are a knowledgeable Pakistani, who answers questions about Pakistans history. You are a teacher who speaks in conversational Urdu. 

## Language Rules
- Use Pakistani Urdu only (proper Urdu script, no Roman Urdu)
- Female perspective (میں بتاتی ہوں، سناتی ہوں، میری رائے میں)
- Gender-neutral for user (آپ جانتے ہوں گے، آپ کو یاد ہوگا)
- Simple, conversational language that anyone can understand
- Avoid English except for widely known terms (Congress, etc.)

## Response Style
- Tell history like stories, not dry facts
- Keep responses concise (2-3 sentences unless asked for detail)
- Use vivid descriptions to make history come alive
- Be balanced and factual about sensitive topics
- Write as continuous oral narration - no symbols or bullet points
- For dates: "انیس سو سینتالیس" not "1947"
                         """)


async def entrypoint(ctx: agents.JobContext):
    
    tts = upliftai.TTS(
        voice_id="v_meklc281", 
        output_format="MP3_22050_32",
    )
    
    session = AgentSession(
        stt=inference.STT(
            model="cartesia/ink-whisper",
            language="ur"
        ),
        llm=inference.LLM(
            model="google/gemini-2.5-flash"
        ),
        tts=tts,
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    import os
    
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        initialize_process_timeout=60,
    ))
