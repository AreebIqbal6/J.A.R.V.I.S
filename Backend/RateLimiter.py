import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse

class TokenBucketRateLimiter:
    def __init__(self, requests_per_minute: int = 120):
        self.rpm = requests_per_minute
        self.capacity = requests_per_minute
        self.tokens = defaultdict(lambda: float(requests_per_minute))
        self.last_update = defaultdict(time.time)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        elapsed = now - self.last_update[client_ip]
        self.last_update[client_ip] = now
        
        # Replenish tokens
        self.tokens[client_ip] = min(float(self.capacity), self.tokens[client_ip] + elapsed * (self.rpm / 60.0))
        
        if self.tokens[client_ip] >= 1.0:
            self.tokens[client_ip] -= 1.0
            return True
        return False

limiter = TokenBucketRateLimiter(requests_per_minute=120)

async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    # Whitelist static assets, health probes and websocket handshake
    if (
        path in ["/api/health", "/health", "/metrics", "/style.css", "/app.js", "/favicon.ico"]
        or path.startswith("/static")
        or path.startswith("/api/ws")
    ):
        return await call_next(request)

    client_ip = request.client.host if request.client else "127.0.0.1"
    if not limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. System protected under industrial rate threshold.",
                "retry_after": 5
            },
            headers={"Retry-After": "5"}
        )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
