import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import MutableHeaders
from prometheus_client import Counter, Histogram, Summary, CollectorRegistry

from .consts import LOGGER


REGISTRY = CollectorRegistry()


# Global metrics objects
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)
HTTP_REQUEST_SIZE = Summary(
    'http_request_size',
    'Size of HTTP requests in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)
HTTP_RESPONSE_SIZE = Summary(
    'http_response_size',
    'Size of HTTP responses in bytes',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)
HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect Prometheus metrics for HTTP requests.

    Requests are tracked for total count, size, duration, and response size.
    WebSocket connections and SSE connections are ignored.
    """

    @staticmethod
    async def _get_response_body(response: Response) -> bytes:
        if hasattr(response, 'body_iterator'):
            try:
                body = b''.join([chunk async for chunk in response.body_iterator])

                # Reset the streaming iterator
                async def body_iterator():
                    yield body

                response.body_iterator = body_iterator()

                return body
            except Exception as e:
                LOGGER.error('Failed to process StreamingResponse body: %s', e)
                return b''

        if hasattr(response, 'body'):
            return response.body

        return b''

    async def dispatch(self,
                       request: Request,
                       call_next: RequestResponseEndpoint
                       ) -> Response:
        method = request.method

        # Try to use the template path if available
        path = request.scope.get('route').path if request.scope.get('route') else request.url.path

        if path.startswith('/metrics'):
            return await call_next(request)

        is_websocket = request.headers.get('upgrade', '').lower() == 'websocket'

        if not is_websocket:
            try:
                body = await request.body()
                HTTP_REQUEST_SIZE.labels(method=method, endpoint=path).observe(len(body))
                request._receive = self.receive_stream_once(body)
            except Exception as e:
                LOGGER.error('Failed to read request body: %s', e)

        start_time = time.monotonic()

        try:
            response = await call_next(request)
        except Exception as e:
            LOGGER.exception('Error processing request %s %s: %s', method, path, e)
            raise e
        finally:
            duration = time.monotonic() - start_time

        status_code = response.status_code
        headers = MutableHeaders(response.headers)
        is_sse = headers.get('content-type') == 'text/event-stream'

        if not is_websocket and not is_sse:
            try:
                body = await self._get_response_body(response)
                HTTP_RESPONSE_SIZE.labels(method=method, endpoint=path, status_code=status_code).observe(len(body))
            except Exception as e:
                LOGGER.error('Failed to read response body: %s', e)

            try:
                HTTP_REQUEST_DURATION.labels(method=method, endpoint=path, status_code=status_code).observe(duration)
            except Exception as e:
                LOGGER.error('Failed to record request duration: %s', e)

        try:
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status_code=status_code).inc()
        except Exception as e:
            LOGGER.error('Failed to increment request counter: %s', e)

        return response

    @staticmethod
    def receive_stream_once(body: bytes) -> Callable:
        """
        Replaces request._receive with a new stream that only yields the original body once.
        """
        sent = False

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        return receive
