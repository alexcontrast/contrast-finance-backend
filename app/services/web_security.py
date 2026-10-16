import re
import secrets
from starlette.responses import HTMLResponse as BaseHTMLResponse, JSONResponse


class SecureHTMLResponse(BaseHTMLResponse):
    def __init__(self, content=None, status_code=200, headers=None, media_type=None, background=None):
        nonce = secrets.token_urlsafe(24)
        if isinstance(content, str):
            content = re.sub(r"<script(?=[\s>])", f'<script nonce="{nonce}"', content, flags=re.I)
        super().__init__(content, status_code=status_code, headers=headers, media_type=media_type, background=background)
        self.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'nonce-{nonce}' 'strict-dynamic' 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; worker-src 'self' blob: https://cdn.jsdelivr.net; "
            "connect-src 'self' https://cdn.jsdelivr.net https://tessdata.projectnaptha.com wss://127.0.0.1:13579; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'"
        )


class RequestBoundsMiddleware:
    def __init__(self, app, max_body_bytes=25 * 1024 * 1024):
        self.app, self.limit = app, max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid Content-Length"}, 400)(scope, receive, send)
        if length > self.limit or length < 0:
            return await JSONResponse({"detail": "Файл или запрос слишком большой"}, 413)(scope, receive, send)
        consumed = 0
        async def bounded_receive():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self.limit:
                    from starlette.exceptions import HTTPException
                    raise HTTPException(413, "Файл или запрос слишком большой")
            return message
        async def secured_send(message):
            if message["type"] == "http.response.start":
                extra = [(b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"same-origin"),
                         (b"x-frame-options", b"SAMEORIGIN")]
                if b"authorization" in headers or scope["path"].startswith("/sign/"):
                    extra.append((b"cache-control", b"private, no-store"))
                existing = list(message.get("headers", []))
                names = {k for k, _ in extra}
                message["headers"] = [(k, v) for k, v in existing if k not in names] + extra
            await send(message)
        await self.app(scope, bounded_receive, secured_send)
