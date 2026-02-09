from livekit.agents import AgentTask, function_tool
from utils.models import EmergencyInfoResult

class CollectEmergencyInfo(AgentTask[EmergencyInfoResult]):
    def __init__(self, chat_ctx=None, ):
        super().__init__(
            instructions="""
            آپ ایک ایمرجنسی ڈسپیچر کا کردار ادا کر رہے ہیں۔
            آپ کا کام یہ ہے کہ کال کرنے والے سے سکون اور پروفیشنل انداز میں اہم معلومات حاصل کریں۔

            اہم ترجیحات:
            1. مقام (پورا پتہ، نزدیکی سڑکیں یا نمایاں نشانی).
            2. ایمرجنسی کی نوعیت (طبی، آگ، جرم، حادثہ وغیرہ).
            3. کال بیک فون نمبر.
            4. شامل افراد کی معلومات (کتنے لوگ ہیں، ان کی حالت).
            5. فوری خطرات (ہتھیار، آگ، گیس لیک، یا دیگر خطرناک صورتحال).

            جب یہ بنیادی معلومات حاصل ہو جائیں تو آپ مزید تفصیل لے سکتے ہیں،
            جیسے مریض کی عمر/جنس، مشتبہ شخص کی تفصیل، خطرات، یا ریسکیو ٹیم کے داخلے کی ہدایات۔

            کال کرنے والے پر نام، واقعہ کی وجوہات یا غیر ضروری تفصیلات کے لئے دباؤ نہ ڈالیں۔
            کالر کو پرسکون رکھیں اور یقین دلائیں کہ "مدد راستے میں ہے"۔
            """,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
            کال کا آغاز اس طرح کریں کہ آپ ایمرجنسی سروسز سے بات کر رہے ہیں۔
            سب سے پہلے ان سے مقام کے بارے میں پوچھیں۔
            سوالات مختصر، واضح اور پرسکون رکھیں۔
            """
        )

    @function_tool
    async def info_collected(
        self,
        location: str,
        emergency_type: str,
        phone: str,
        people_involved: str,
        safety_concerns: str,
        extra_details: str = "",
    ) -> None:
        """Complete task once all essential info is gathered"""
        result = EmergencyInfoResult(
            location=location,
            emergency_type=emergency_type,
            phone=phone,
            people_involved=people_involved,
            safety_concerns=safety_concerns,
            extra_details=extra_details,
        )
        self.complete(result)


