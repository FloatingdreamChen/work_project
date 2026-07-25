from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import Request, Response, status

from backend.config import get_settings


class ConcurrencyLimiter:
    def __init__(self, limit: int) -> None:
        self._semaphore = asyncio.Semaphore(max(1, limit))

    async def __call__(self, request: Request, call_next):
        if self._semaphore.locked():
            return Response("系统繁忙，请稍后再试", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        async with self._semaphore:
            return await call_next(request)


def configure_loop_executor() -> None:
    loop = asyncio.get_running_loop()
    settings = get_settings()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=max(2, settings.worker_thread_pool_size)))
