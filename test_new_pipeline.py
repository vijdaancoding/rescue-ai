#!/usr/bin/env python3
"""
Test script for the new conversational pipeline
"""
import json
from config import Config
from generator import ConversationGenerator
from utils import validate_conversation_turn, convert_to_messages_format

def test_single_generation():
    """Test generating a single batch"""
    print("🧪 Testing new conversational pipeline...")
    
    # Test scenarios
    test_scenarios = [
        {
            "city": "Lahore",
            "area": "Gulberg", 
            "emergency": "دل کا دورہ",
            "caller_state": "گھبرایا ہوا",
            "message_type": "initial_call",
            "emergency_category": "medical"
        },
        {
            "city": "Karachi",
            "area": "Clifton",
            "emergency": "آگ",
            "caller_state": "پریشان", 
            "message_type": "location_info",
            "emergency_category": "fire"
        },
        {
            "city": "Islamabad",
            "area": "F-7",
            "emergency": "ٹریفک حادثہ",
            "caller_state": "درد میں",
            "message_type": "urgency",
            "emergency_category": "accident"
        }
    ]
    
    try:
        turns = ConversationGenerator.fetch_batch(test_scenarios)
        print(f"✅ Generated {len(turns)} conversation turns")
        
        valid_count = 0
        
        for i, turn in enumerate(turns):
            print(f"\n--- Turn {i+1} ---")
            print(f"User: {turn.user_message}")
            print(f"Assistant: {turn.assistant_response}")
            print(f"Context: {turn.context}")
            
            # Validate
            is_valid = validate_conversation_turn(turn)
            print(f"Valid: {is_valid}")
            
            if is_valid:
                valid_count += 1
                # Show messages format
                messages_format = convert_to_messages_format(turn)
                print(f"Messages format: {json.dumps(messages_format, ensure_ascii=False, indent=2)}")
        
        print(f"\n📊 Summary:")
        print(f"Valid turns: {valid_count}/{len(turns)}")
        
        return valid_count > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_sample_formats():
    """Show what the final format looks like"""
    print("\n📝 Expected final format for fine-tuning:")
    
    sample = {
        "messages": [
            {
                "role": "user",
                "content": "ہیلو، مجھے مدد چاہیے! میرے والد کو دل کا دورہ پڑا ہے!"
            },
            {
                "role": "assistant",
                "content": "آپ کہاں ہیں؟ مکمل پتہ بتائیں تاکہ ایمبولینس بھیج سکیں۔"
            }
        ]
    }
    
    print(json.dumps(sample, ensure_ascii=False, indent=2))
    
    print("\n✅ This format is perfect for:")
    print("- Alif 8B fine-tuning")
    print("- Llama-based models")
    print("- Conversational AI training")
    print("- Single-turn response training")

if __name__ == "__main__":
    print("🚀 Testing New Conversational Pipeline")
    
    # Test generation
    success = test_single_generation()
    
    # Show format
    show_sample_formats()
    
    if success:
        print("\n✅ New pipeline test successful! Ready for full generation.")
        print(f"🎯 Will generate {Config.TARGET_ROWS} conversation turns")
    else:
        print("\n❌ Pipeline test failed. Check configuration.")