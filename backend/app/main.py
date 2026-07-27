from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.errors import AppError
from app.core.request_context import get_request_id
from app.core.schemas import ErrorDetail, ErrorResponse
from app.db.session import create_tables, dispose_engine
from app.middleware.request_id import RequestIdMiddleware

logger = logging.getLogger("ai-platform")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        await create_tables()
    yield
    await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="公司内部统一 AI 能力服务",
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs", "health": "/api/v1/system/health"}


@app.exception_handler(AppError)
async def handle_app_error(_: Request, error: AppError) -> JSONResponse:
    payload = ErrorResponse(
        request_id=get_request_id(),
        error=ErrorDetail(
            code=error.code.value,
            message=error.message,
            retryable=error.retryable,
        ),
    )
    return JSONResponse(status_code=error.http_status, content=payload.model_dump(by_alias=True))


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        request_id=get_request_id(),
        error=ErrorDetail(
            code=ErrorCode.INVALID_REQUEST.value,
            message="请求参数格式不正确",
            retryable=False,
        ),
    )
    return JSONResponse(status_code=422, content=payload.model_dump(by_alias=True))


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, error: Exception) -> JSONResponse:
    logger.exception("Unhandled error request_id=%s error_type=%s", get_request_id(), type(error).__name__)
    payload = ErrorResponse(
        request_id=get_request_id(),
        error=ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="AI Agent 中台内部错误",
            retryable=False,
        ),
    )
    return JSONResponse(status_code=500, content=payload.model_dump(by_alias=True))
