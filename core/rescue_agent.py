import logging
from livekit.agents import Agent
from livekit.agents.llm import ChatContext
from tasks import CollectEmergencyInfo

logger = logging.getLogger("emergency-agent")

class EmergencyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "آپ ایک ہیلپ لائن آپریٹر ہیں جو 1122/911 کی ایمرجنسی کالز پر جواب دیتا ہے۔ "
                "آپ کا لہجہ پرسکون، ہمدرد اور پیشہ ورانہ ہونا چاہیے۔ "
                "ہمیشہ اردو میں بات کریں۔ "
                "آپ کا مقصد ہے: "
                "١) کال کرنے والے کو تسلی دینا اور گھبرانے نہ دینا۔ "
                "٢) فوراً ایمرجنسی کی نوعیت پوچھنا (آگ، حادثہ، طبی مسئلہ وغیرہ)۔ "
                "٣) ان کا درست مقام معلوم کرنا۔ "
                "٤) متاثرہ افراد کی تعداد پوچھنا۔ "
                "ہمیشہ ایمرجنسی کی معلومات واضح اور مرحلہ وار لیں، اور کالر کو بتائیں کہ امدادی ٹیم راستے میں ہے۔"
            )
        )

    async def on_enter(self) -> None:  

        result = await CollectEmergencyInfo(chat_ctx=self.chat_ctx)

        history_records = [
            {"role": item.role, "content": item.content}
            for item in self.chat_ctx.items
        ]

        if not result:
            await self.session.generate_reply(instructions="Inform the user that you are unable to proceed and will end the call.")
        else:
            await self.session.generate_reply(
                            instructions="Say this in a reassuring tone in Urdu: 'Thank you for the information. The emergency team has been dispatched to your location. Please stay safe. Goodbye.'"
                        )
        
        logger.info(f"Emergency info collected: {result}")
        logger.info(f"Chat history (len={len(history_records)}): {history_records}")

    
    async def llm_node(self, chat_ctx: ChatContext, tools: None = None, tool_choice: str | None = None):
        """
        This method processes the LLM stream.
        It yields each chunk of text as it is received from the LLM.
        """
        async with self.llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=tool_choice) as stream:
            async for chunk in stream:
                yield chunk

