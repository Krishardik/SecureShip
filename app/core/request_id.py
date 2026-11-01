import logging
from uuid import uuid4

security_logger = logging.getLogger("secureship.security")


class RequestIDMiddleware:
    """Generate and propagate a unique server-side ID for every HTTP request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())

        # Make the ID available through request.state.request_id.
        scope.setdefault("state", {})["request_id"] = request_id

        response_status = None

        async def send_with_request_id(message):
            nonlocal response_status

            if message["type"] == "http.response.start":
                response_status = message["status"]

                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))

                message = {**message, "headers": headers}

            await send(message)

        await self.app(scope, receive, send_with_request_id)

        security_logger.info(
            "HTTP request completed",
            extra={
                "event": "http.request.completed",
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
                "status_code": response_status,
            },
        )
