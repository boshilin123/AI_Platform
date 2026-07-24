from contextvars import ContextVar
from uuid import uuid4


request_id_context: ContextVar[str] = ContextVar("request_id", default="")


def new_request_id() -> str:
    return f"ai-{uuid4().hex}"


def get_request_id() -> str:
    return request_id_context.get() or new_request_id()
