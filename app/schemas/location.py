from pydantic import BaseModel, Field


class LocationPayload(BaseModel):
    phone_number: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class LocationResponse(BaseModel):
    status: str
    message: str


class AnalysisRequest(BaseModel):
    transcript: str = Field(min_length=1)
