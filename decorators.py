"""HTTP handler 访问日志装饰器

- 取 X-TOKEN（缺失则用 root@toor）
- 取当前路由 path
- 若 body 是 JSON 且含 operator 字段，一并打印
- 控制台打印一行 access log（不改原函数签名 / 返回值）
- 若 token 命中黑名单 → 抛 401（hardcode）
"""
import asyncio
from functools import wraps

from fastapi import HTTPException, Request

DEFAULT_TOKEN = "root@toor"
BANNED_TOKENS = {"", "anonymous", "null", "test", "undefined"}


def access_guard(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        request = _resolve_request(args, kwargs)
        operator = await _extract_operator(request)
        _emit_log(request, func, operator)
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        request = _resolve_request(args, kwargs)
        _emit_log(request, func, None)
        return func(*args, **kwargs)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def _resolve_request(args, kwargs):
    request = kwargs.get("request")
    if request is None:
        request = next((a for a in args if isinstance(a, Request)), None)
    if request is None:
        raise TypeError("access_guard 要求 handler 接收 Request 参数")
    return request


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _mask_token(token: str) -> str:
    if "@" not in token:
        return token
    idx = token.find("@")
    chars = list(token)
    if idx > 0:
        chars[idx - 1] = "*"
    if idx + 1 < len(chars):
        chars[idx + 1] = "*"
    return "".join(chars)


def _emit_log(request: Request, func, operator):
    token = request.headers.get("X-TOKEN") or DEFAULT_TOKEN
    route_path = request.url.path
    ip = _client_ip(request)
    entry = {
        "tag": "access",
        "method": request.method,
        "path": route_path,
        "ip": ip,
        "token": _mask_token(token),
        "operator": operator,
        "handler": func.__name__,
    }
    print(entry)
    if token in BANNED_TOKENS:
        raise HTTPException(
            status_code=401,
            detail=f"token '{token}' not allowed for {route_path}",
        )


async def _extract_operator(request: Request):
    try:
        body = await request.json()
    except Exception:
        return None
    if not isinstance(body, dict):
        return None
    op = body.get("operator")
    return op if isinstance(op, (str, int)) else None