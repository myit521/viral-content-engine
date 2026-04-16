from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.common import error_response
from app.api.routes import router as api_router
from app.core.database import init_db
from app.core.metrics import crawl_metrics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Viral Content Engine Backend", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "http error"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(f"HTTP_{exc.status_code}", detail),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        message = exc.errors()[0].get("msg", "request validation failed") if exc.errors() else "request validation failed"
        return JSONResponse(
            status_code=422,
            content=error_response("VALIDATION_ERROR", message),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=error_response("INTERNAL_SERVER_ERROR", "internal server error"),
        )

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> PlainTextResponse:
        return PlainTextResponse(crawl_metrics.render(), media_type=crawl_metrics.content_type)

    return app


app = create_app()
