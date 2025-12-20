import re
import logging
import random
from typing import List
from schemas import ConversationTurn

# Setup Logging
logging.basicConfig(
    filename='pipeline.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def contains_english(text: str) -> bool:
    """Returns True if the text contains English letters."""
    return bool(re.search(r'[a-zA-Z]', text))

def validate_conversation_turn(turn: ConversationTurn) -> bool:
    """
    Validate a single conversation turn
    """
    # Check for English characters
    if contains_english(turn.user_message) or contains_english(turn.assistant_response):
        logging.warning(f"English detected in turn")
        return False
    
    # Check minimum length
    if len(turn.user_message.strip()) < 5 or len(turn.assistant_response.strip()) < 5:
        logging.warning(f"Turn too short")
        return False
    
    # Check maximum length (avoid overly long messages)
    if len(turn.user_message.split()) > 35 or len(turn.assistant_response.split()) > 30:
        logging.warning(f"Turn too long")
        return False
    
    # Check for meaningful content (not just punctuation)
    if not re.search(r'[\u0600-\u06FF]', turn.user_message) or not re.search(r'[\u0600-\u06FF]', turn.assistant_response):
        logging.warning(f"No Urdu content found")
        return False
    
    return True

def convert_to_messages_format(turn: ConversationTurn) -> dict:
    """
    Convert conversation turn to messages format for fine-tuning
    """
    return {
        "messages": [
            {
                "role": "user",
                "content": turn.user_message
            },
            {
                "role": "assistant", 
                "content": turn.assistant_response
            }
        ]
    }

def create_signature(turn: ConversationTurn) -> str:
    """Create a unique signature for deduplication"""
    # Use first 50 chars of user message + first 30 chars of response
    user_part = turn.user_message[:50].strip()
    assistant_part = turn.assistant_response[:30].strip()
    return f"{user_part}|{assistant_part}"