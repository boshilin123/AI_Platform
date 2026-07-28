from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SpeechSynthesisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=50_000)
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "alloy"
    response_format: Literal["mp3", "wav"] = Field(default="mp3", alias="responseFormat")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text is required")
        return normalized
