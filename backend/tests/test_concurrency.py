import asyncio

from starlette.requests import Request

from backend.core.concurrency import ConcurrencyLimiter


def test_concurrency_limiter_returns_503_when_full() -> None:
    limiter = ConcurrencyLimiter(limit=1)

    async def run():
        await limiter._semaphore.acquire()
        try:
            scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
            response = await limiter(Request(scope), lambda request: None)
            return response.status_code
        finally:
            limiter._semaphore.release()

    assert asyncio.run(run()) == 503
