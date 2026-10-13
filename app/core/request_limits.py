from starlette.requests import Request
from starlette.responses import JSONResponse


class RequestSizeLimitMiddleware:
    """Reject requests whose declared or received body exceeds the limit."""

    def __init__(self, app, max_body_bytes: int = 1_048_576):
        if max_body_bytes <= 0:
            raise ValueError("max_body_bytes must be positive")

        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"},
                )
                await response(scope, receive, send)
                return

            if declared_size < 0:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"},
                )
                await response(scope, receive, send)
                return

            if declared_size > self.max_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
                await response(scope, receive, send)
                return

        received_size = 0
        body_chunks = []

        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")
            received_size += len(chunk)

            if received_size > self.max_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
                await response(scope, receive, send)
                return

            body_chunks.append(chunk)

            if not message.get("more_body", False):
                break

        body = b"".join(body_chunks)
        sent = False

        async def replay_receive():
            nonlocal sent

            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}

            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay_receive, send)
