from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class ConversationTurn(BaseModel):
    """Single conversation turn for fine-tuning format"""
    user_message: str = Field(..., description="User's message in Urdu")
    assistant_response: str = Field(..., description="Assistant's response in Urdu")
    context: str = Field(default="", description="Optional context about the emergency situation")

class EmergencyConversation(BaseModel):
    """Collection of conversation turns for a single emergency scenario"""
    scenario: str = Field(..., description="Emergency scenario description")
    turns: List[ConversationTurn] = Field(..., description="List of conversation turns")

class AlifTrainingRow(BaseModel):
    """Final training format for Alif model"""
    messages: List[dict] = Field(..., description="Conversation in messages format")