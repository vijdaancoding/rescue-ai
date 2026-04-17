from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    is_active: bool
