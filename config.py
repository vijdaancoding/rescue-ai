import os
import random

# Enhanced Pakistani locations with specific landmarks
LOCATIONS = {
    "Lahore": ["Gulberg", "DHA", "Johar Town", "Model Town", "Anarkali", "Liberty Market", "Mall Road", "Kalma Chowk"],
    "Karachi": ["Clifton", "Defence", "Gulshan", "North Nazimabad", "Saddar", "Korangi", "Malir", "Lyari"],
    "Islamabad": ["F-6", "F-7", "F-8", "G-9", "Blue Area", "Margalla Hills", "Sector I-8", "Constitution Avenue"],
    "Rawalpindi": ["Saddar", "Committee Chowk", "Raja Bazaar", "Cantonment", "Satellite Town", "Chaklala"],
    "Faisalabad": ["Ghulam Muhammad Abad", "Peoples Colony", "Samanabad", "Millat Town", "Jaranwala Road"],
    "Multan": ["Cantt", "Gulgasht Colony", "New Multan", "Shah Rukn-e-Alam Colony", "Bosan Road"],
    "Peshawar": ["University Town", "Hayatabad", "Board Bazaar", "Saddar", "Ring Road", "GT Road"],
    "Quetta": ["Cantonment", "Satellite Town", "Brewery Road", "Jinnah Road", "Samungli Road"],
    "Gujranwala": ["Civil Lines", "Model Town", "Satellite Town", "GT Road", "Wapda Town"],
    "Sialkot": ["Cantonment", "Paris Road", "Kutchery Road", "Circular Road", "Rangpura"]
}

# Emergency types with Pakistani context
EMERGENCY_TYPES = {
    "medical": [
        "دل کا دورہ", "سانس کی تکلیف", "بے ہوشی", "زہر کھانا", "حمل کی پیچیدگی", 
        "ذیابیطس کا کوما", "بلڈ پریشر", "دمہ کا حملہ", "کھانسی اور بخار", "چکر آنا"
    ],
    "fire": [
        "گھر میں آگ", "دکان میں آگ", "گاڑی میں آگ", "کارخانے میں آگ", 
        "جنگل کی آگ", "بجلی کی تار سے آگ", "گیس سلنڈر پھٹنا"
    ],
    "crime": [
        "ڈکیتی", "چوری", "اغوا", "قتل کی کوشش", "گھریلو تشدد", 
        "عصمت دری", "دھمکی", "جعلی پولیس", "موبائل چھیننا"
    ],
    "accident": [
        "ٹریفک حادثہ", "موٹرسائیکل حادثہ", "بس حادثہ", "ٹرک حادثہ", 
        "کام کے دوران حادثہ", "گرنا", "کنویں میں گرنا", "بلڈنگ سے گرنا"
    ],
    "natural": [
        "سیلاب", "زلزلہ", "آندھی طوفان", "بارش کا نقصان", 
        "بجلی گرنا", "درخت گرنا", "دیوار گرنا", "چھت گرنا"
    ],
    "utility": [
        "گیس لیکج", "بجلی کا جھٹکا", "پانی کی کمی", "سیوریج کا مسئلہ", 
        "ٹرانسفارمر پھٹنا", "بجلی کی تار ٹوٹنا"
    ]
}

# Caller emotional states
CALLER_STATES = {
    "panic": ["گھبرایا ہوا", "پریشان", "ڈرا ہوا", "بے قابو", "رو رہا ہے"],
    "pain": ["درد میں", "تکلیف میں", "زخمی", "بے ہوش", "کمزور"],
    "angry": ["غصے میں", "ناراض", "چیخ رہا ہے", "بدتمیز", "جلدی میں"],
    "calm": ["پرسکون", "سنجیدہ", "صاف بات کرنے والا", "تعاون کرنے والا"]
}

# Message types for variety
MESSAGE_TYPES = [
    "initial_call",      # First emergency call
    "location_info",     # Providing location
    "details",          # Emergency details
    "follow_up",        # Follow-up questions
    "urgency",          # Expressing urgency
    "additional_info",   # Extra information
    "confirmation",     # Confirming details
    "status_check"      # Checking status
]

def generate_conversation_scenarios(count=500):
    """Generate scenarios for single-turn conversations"""
    scenarios = []
    
    for _ in range(count):
        city = random.choice(list(LOCATIONS.keys()))
        area = random.choice(LOCATIONS[city])
        emergency_cat = random.choice(list(EMERGENCY_TYPES.keys()))
        emergency = random.choice(EMERGENCY_TYPES[emergency_cat])
        caller_state = random.choice(list(CALLER_STATES.keys()))
        state_desc = random.choice(CALLER_STATES[caller_state])
        message_type = random.choice(MESSAGE_TYPES)
        
        scenario = {
            "city": city,
            "area": area,
            "emergency": emergency,
            "caller_state": state_desc,
            "message_type": message_type,
            "emergency_category": emergency_cat
        }
        
        scenarios.append(scenario)
    
    return scenarios

class Config:
    # API Settings
    API_KEY = os.getenv("GCP_API_KEY") 
    MODEL_NAME = "gemini-2.0-flash-lite"
    
    # Generation Settings
    BATCH_SIZE = 15            # Generate more single turns per batch
    TARGET_ROWS = 5000          # Target 500 conversation turns
    MAX_RETRIES = 5           
    OUTPUT_FILE = "data/alif_conversational_train.jsonl"
    LOG_FILE = "pipeline.log"
    
    # System Instruction for Single-Turn Conversations
    SYSTEM_INSTRUCTION = (
        "آپ پاکستان کے Rescue 1122 کے لیے single-turn مکالمے تیار کرنے والے AI ہیں۔"
        "\n\n### مقصد ###"
        "ہر scenario کے لیے مختلف قسم کے user messages اور operator responses بنائیں۔"
        
        "\n\n### فارمیٹ ###"
        "ہر conversation turn میں:"
        "\n- user_message: کال کرنے والے کا پیغام (اردو میں)"
        "\n- assistant_response: Rescue 1122 operator کا جواب (اردو میں)"
        "\n- context: حالات کی مختصر تفصیل"
        
        "\n\n### مختلف قسم کے User Messages ###"
        "\n1. ابتدائی کال: 'ہیلو، مجھے مدد چاہیے، میرے والد کو دل کا دورہ پڑا ہے'"
        "\n2. مقام بتانا: 'میں لاہور کے گلبرگ میں ہوں، گھر نمبر 123'"
        "\n3. تفصیلات: 'وہ بے ہوش ہیں اور سانس نہیں لے رہے'"
        "\n4. فالو اپ: 'ایمبولینس کتنی دیر میں آئے گی؟'"
        "\n5. اضافی معلومات: 'مریض کی عمر 65 سال ہے اور شوگر کا مریض ہے'"
        "\n6. پریشانی: 'جلدی کریں، حالت بہت خراب ہو رہی ہے'"
        "\n7. تصدیق: 'جی ہاں، میں نے CPR شروع کر دیا ہے'"
        "\n8. سوال: 'مجھے کیا کرنا چاہیے؟'"
        
        "\n\n### Operator Responses ###"
        "\n1. سوال پوچھنا: 'آپ کہاں ہیں؟ مکمل پتہ بتائیں'"
        "\n2. تصدیق: 'ایمبولینس روانہ کر دی گئی ہے، 5-7 منٹ میں پہنچے گی'"
        "\n3. ہدایات: 'مریض کو آرام سے لٹا دیں اور سر کو ایک طرف کر دیں'"
        "\n4. تسلی: 'فکر نہ کریں، مدد آ رہی ہے، آپ بہت اچھا کر رہے ہیں'"
        "\n5. اضافی سوالات: 'کیا مریض ہوش میں ہے؟ کیا وہ بات کر سکتے ہیں؟'"
        "\n6. CPR ہدایات: 'سینے کے بیچ میں دونوں ہاتھ رکھ کر زور سے دبائیں'"
        "\n7. انتظار: 'لائن پر رہیں، میں آپ کو مزید ہدایات دیتا ہوں'"
        "\n8. حوصلہ افزائی: 'آپ بہت بہادری سے کام کر رہے ہیں'"
        
        "\n\n### اہم ###"
        "\n- صرف اردو استعمال کریں"
        "\n- ہر turn منفرد ہو"
        "\n- حقیقی پاکستانی حالات"
        "\n- مختلف جذباتی states"
        "\n- مختلف emergency types"
        "\n- مختلف message types"
    )

    # Generate diverse scenarios
    SCENARIOS = generate_conversation_scenarios(1000)