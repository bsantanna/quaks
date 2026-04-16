import re

from pydantic import BaseModel, field_validator


class WaitlistRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    username: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be empty")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Username must not be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Username must contain only lowercase letters, numbers, hyphens, or underscores"
            )
        return v


class WaitlistResponse(BaseModel):
    status: str
