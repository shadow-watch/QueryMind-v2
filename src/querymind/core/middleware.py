import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from querymind.core.settings import settings

logger = logging.getLogger("querymind.request")


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def attach_request_id_filter() -> None:
    root = logging.getLogger()
    already = any(isinstance(f, RequestIDFilter) for f in root.filters)
    if not already:
        root.addFilter(RequestIDFilter())


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start = time.perf_counter()
    request_id = request.headers.get(settings.request_id_header) or str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        "request_start method=%s path=%s",
        request.method,
        request.url.path,
        extra={"request_id": request_id},
    )

    response = await call_next(request)
    response.headers[settings.request_id_header] = request_id

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request_end method=%s path=%s status=%s elapsed_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        extra={"request_id": request_id},
    )
    return response
