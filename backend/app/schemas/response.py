from typing import Any, Optional

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str


class APIResponse(BaseModel):
    ok: bool
    data: Optional[Any]
    error: Optional[ErrorBody]


def success_response(data: Any = None) -> dict:
    """标准成功响应。"""
    return {"ok": True, "data": data, "error": None}


def error_response(code: str, message: str) -> dict:
    """标准失败响应。"""
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}


