from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import settings


class AssistantRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[UUID, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, user_id: UUID) -> None:
        now = monotonic()
        cutoff = now - settings.assistant_rate_limit_window_seconds
        with self._lock:
            requests = self._requests[user_id]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= settings.assistant_rate_limit_requests:
                retry_after = max(1, int(requests[0] + settings.assistant_rate_limit_window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Assistant request rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )
            requests.append(now)


assistant_rate_limiter = AssistantRateLimiter()
