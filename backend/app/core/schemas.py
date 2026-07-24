from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=lambda name: _to_camel(name))


class ErrorDetail(CamelModel):
    code: str
    message: str
    retryable: bool


class SuccessResponse(CamelModel, Generic[T]):
    success: bool = True
    request_id: str
    data: T


class ErrorResponse(CamelModel):
    success: bool = False
    request_id: str
    error: ErrorDetail
