from dataclasses import dataclass
from typing import Optional

@dataclass
class EmergencyInfoResult:
    location: Optional[str] = None
    emergency_type: Optional[str] = str
    phone: Optional[str] = None
    people_involved: Optional[str] = None
    safety_concerns: Optional[str] = None
    extra_details: Optional[str] = None

