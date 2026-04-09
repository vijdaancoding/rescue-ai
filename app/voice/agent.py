from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, WorkerType, inference
from livekit.plugins import upliftai, silero

AGENT_NAME = "rescue-operator"


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
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
- پتہ اور قریبی نشان دہی لازمی لیں
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
        """)


async def entrypoint(ctx: agents.JobContext):
    tts = upliftai.TTS(
        voice_id="v_meklc281",
        output_format="MP3_22050_32",
    )

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general:hi"),
        llm=inference.LLM(model="google/gemini-3-flash"),
        tts=tts,
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(),
    )

    await session.generate_reply(
        instructions="ہیلپ لائن آپریٹر کے طور پر کالر کو اردو میں خوش آمدید کہیں۔"
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name=AGENT_NAME,
        worker_type=WorkerType.ROOM,
        initialize_process_timeout=60,
    ))
