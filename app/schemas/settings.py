from pydantic import BaseModel, ConfigDict
from typing import Optional


class SettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = None
    email: Optional[str] = None
    sound_alerts: bool = True
    email_notifications: bool = True
    emergency_alerts: bool = True
    language: str = "english"
    volume: int = 75
    microphone: bool = True
    two_factor_auth: bool = False
    session_timeout: int = 30


class SettingsUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    sound_alerts: Optional[bool] = None
    email_notifications: Optional[bool] = None
    emergency_alerts: Optional[bool] = None
    language: Optional[str] = None
    volume: Optional[int] = None
    microphone: Optional[bool] = None
    two_factor_auth: Optional[bool] = None
    session_timeout: Optional[int] = None
