from __future__ import annotations

from uuid import uuid4


def success_response(data: object, message: str = "success") -> dict:
    return {
        "code": "OK",
        "message": message,
        "data": data,
        "request_id": f"req_{uuid4().hex[:12]}",
    }


def error_response(code: str, message: str) -> dict:
    return {
        "code": code,
        "message": message,
        "data": None,
        "request_id": f"req_{uuid4().hex[:12]}",
    }

