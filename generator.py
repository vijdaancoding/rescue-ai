import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google import genai
from google.genai import types
from config import Config
from schemas import ConversationTurn

# Initialize Client
client = genai.Client(api_key=Config.API_KEY)

class ConversationGenerator:
    
    @staticmethod
    def create_detailed_prompt(scenarios: list) -> str:
        """Create a detailed prompt for single-turn conversation generation"""
        
        prompt = f"""
آپ کو {len(scenarios)} منفرد conversation turns بنانے ہیں۔

ہر scenario کے لیے ایک user message اور ایک assistant response بنائیں:

"""
        
        for i, scenario in enumerate(scenarios, 1):
            prompt += f"""
Scenario {i}:
- شہر: {scenario['city']}
- علاقہ: {scenario['area']}
- ایمرجنسی: {scenario['emergency']}
- کال کرنے والے کی حالت: {scenario['caller_state']}
- Message Type: {scenario['message_type']}
- Category: {scenario['emergency_category']}

"""
        
        prompt += """
### ضروری ہدایات ###

1. ہر turn میں:
   - user_message: کال کرنے والے کا پیغام (5-30 الفاظ)
   - assistant_response: آپریٹر کا جواب (5-25 الفاظ)
   - context: مختصر حالات (2-10 الفاظ)

2. مختلف قسم کے messages:
   - ابتدائی کال: "ہیلو، مجھے مدد چاہیے..."
   - مقام: "میں [شہر] کے [علاقہ] میں ہوں..."
   - تفصیلات: "میرے [رشتہ] کو [مسئلہ] ہے..."
   - پریشانی: "جلدی کریں، حالت خراب ہے..."
   - سوال: "مجھے کیا کرنا چاہیے؟"

3. آپریٹر responses:
   - سوال: "آپ کہاں ہیں؟"
   - تصدیق: "ایمبولینس روانہ کر دی گئی"
   - ہدایات: "مریض کو آرام سے لٹا دیں"
   - تسلی: "فکر نہ کریں، مدد آ رہی ہے"

4. صرف اردو، کوئی انگریزی نہیں
5. ہر turn منفرد ہو
6. حقیقی پاکستانی ماحول

جواب JSON format میں دیں۔
"""
        return prompt
    
    @staticmethod
    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_batch(scenarios: list) -> list[ConversationTurn]:
        """
        Generate single-turn conversations
        """
        prompt = ConversationGenerator.create_detailed_prompt(scenarios)

        response = client.models.generate_content(
            model=Config.MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=Config.SYSTEM_INSTRUCTION,
                temperature=0.95,  # High temperature for variety
                top_p=0.9,         
                response_mime_type="application/json",
                response_schema=list[ConversationTurn],
            ),
            contents=prompt
        )
        
        if not response.parsed:
            raise ValueError("Empty response from Gemini API")
            
        return response.parsed