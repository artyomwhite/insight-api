"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.schemas.common import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Insight API")
    yield
    logger.info("Shutting down Insight API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
## Insight API

Production-ready **event analytics backend** for tracking business events and powering dashboards.

### Authentication

- **JWT** — dashboard login (`/auth/login`) for analytics and management
- **API Key** — event ingestion (`POST /events`) via `Authorization: Bearer ins_...`

### Quick Start

1. Login: `POST /api/v1/auth/login`
2. Create API key: `POST /api/v1/api-keys`
3. Ingest events: `POST /api/v1/events` with API key
4. Query analytics: `GET /api/v1/analytics/overview`
        """,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        openapi_tags=[
            {"name": "Health", "description": "Service health and readiness probes"},
            {"name": "Authentication", "description": "Dashboard JWT authentication"},
            {"name": "API Keys", "description": "API key management for event ingestion"},
            {"name": "Events", "description": "Event ingestion and querying"},
            {"name": "Analytics", "description": "Aggregations, funnels, and exports"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorBody(
                    code=exc.code,
                    message=exc.message,
                    details=[ErrorDetail(**d) for d in exc.details],
                    request_id=request_id,
                )
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        details = [
            ErrorDetail(
                field=".".join(str(loc) for loc in err.get("loc", [])),
                message=err.get("msg", "Invalid value"),
            )
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorBody(
                    code="VALIDATION_ERROR",
                    message="Request validation failed",
                    details=details,
                    request_id=request_id,
                )
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled error: %s", exc)
        message = "Internal server error" if settings.is_production else str(exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorBody(
                    code="INTERNAL_ERROR",
                    message=message,
                    request_id=request_id,
                )
            ).model_dump(),
        )

    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()
