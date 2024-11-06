from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ConfirmRequest(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    code: str = Field(..., description="Confirmation code")

    class Config:
        model_config = {'from_attributes': True}

class RefreshTokenRequest(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    refreshToken: str = Field(..., description="The refresh token")

    class Config:
        model_config = {'from_attributes': True}

class SigninRequest(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    password: str = Field(..., description="The user's password")

    class Config:
        model_config = {'from_attributes': True}

class SignupRequest(BaseModel):
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name (optional)")
    email: EmailStr = Field(..., description="The email of the user")
    password: str = Field(..., description="The user's password")

    class Config:
        model_config = {'from_attributes': True}

class InitiateResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")

    class Config:
        model_config = {'from_attributes': True}

class ConfirmResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    code: str = Field(..., description="Confirmation code")
    new_password: str = Field(..., description="New password")

    class Config:
        model_config = {'from_attributes': True}
