from pydantic import BaseModel, EmailStr, ConfigDict


class UserProfileUpdateResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
