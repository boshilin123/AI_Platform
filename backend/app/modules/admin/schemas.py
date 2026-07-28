from datetime import datetime

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from app.core.schemas import CamelModel


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: SecretStr

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip()
        if not 1 <= len(normalized) <= 64:
            raise ValueError("username length is invalid")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        if not 1 <= len(value.get_secret_value()) <= 256:
            raise ValueError("password length is invalid")
        return value


class AdminSessionData(CamelModel):
    username: str
    access_token: str
    expires_at: datetime


class AdminSessionStatus(CamelModel):
    username: str
    expires_at: datetime


class AdminLogoutData(CamelModel):
    logged_out: bool
