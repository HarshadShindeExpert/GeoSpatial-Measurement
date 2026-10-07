import time
from collections import defaultdict
from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 120,
        upload_limit_per_minute: int = 20
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.upload_limit_per_minute = upload_limit_per_minute
        self.ip_history = defaultdict(list)
        self.upload_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        one_minute_ago = now - 60.0

        # Clean old timestamps for this IP
        self.ip_history[client_ip] = [t for t in self.ip_history[client_ip] if t > one_minute_ago]

        # Check overall rate limit
        if len(self.ip_history[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Too many requests. Please try again in a minute."}
            )

        # Special rate limit for upload endpoint POST /api/files/
        if request.method == "POST" and "/files" in request.url.path:
            self.upload_history[client_ip] = [t for t in self.upload_history[client_ip] if t > one_minute_ago]
            if len(self.upload_history[client_ip]) >= self.upload_limit_per_minute:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Upload rate limit exceeded. Maximum 20 file uploads per minute allowed."}
                )
            self.upload_history[client_ip].append(now)

        self.ip_history[client_ip].append(now)

        response = await call_next(request)
        return response
