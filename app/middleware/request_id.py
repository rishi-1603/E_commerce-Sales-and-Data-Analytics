from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid
import time
import logging

logger = logging.getLogger("commerce_api")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate X-Request-ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()

        # Pass request down the chain
        response = await call_next(request)

        # Calculate execution latency
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = str(process_time_ms)

        logger.info(
            f"method={request.method} path={request.url.path} status={response.status_code} "
            f"latency_ms={process_time_ms} request_id={request_id}"
        )
        return response
