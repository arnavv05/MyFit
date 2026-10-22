import logging
import time
from collections import defaultdict

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from backend.app.core.config import settings
from backend.app.db.mongodb import connect_to_mongo, close_mongo_connection
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.logs import router as logs_router
from backend.app.api.v1.recommend import router as recommend_router
from backend.app.api.v1.feedback import router as feedback_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.catalog import router as catalog_router

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple in-process rate-limiter for auth routes
# ---------------------------------------------------------------------------
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(key: str, max_requests: int, window_seconds: int) -> None:
    now = time.time()
    timestamps = _rate_store[key]
    # Remove old timestamps outside window
    _rate_store[key] = [t for t in timestamps if now - t < window_seconds]
    if len(_rate_store[key]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
    _rate_store[key].append(now)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – connecting to MongoDB…")
    try:
        await connect_to_mongo()
        logger.info("MongoDB connected.")
    except Exception as exc:
        logger.warning(
            "Initial MongoDB connection failed: %s. Atlas IP Access may be needed; requests will retry.",
            exc,
        )
    yield
    logger.info("Shutting down – closing MongoDB connection…")
    await close_mongo_connection()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Myfitness personalised fitness API. "
        "Authenticate via /api/v1/auth/login to get a Bearer token."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS – locked to configured origins (not wildcard)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth rate-limiting middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def auth_rate_limit_middleware(request: Request, call_next):
    if request.method != "OPTIONS" and request.url.path in (
        f"{settings.API_V1_PREFIX}/auth/login",
        f"{settings.API_V1_PREFIX}/auth/register",
    ):
        client_ip = request.client.host if request.client else "unknown"
        try:
            _check_rate_limit(
                f"auth:{client_ip}",
                settings.AUTH_RATE_LIMIT_REQUESTS,
                settings.AUTH_RATE_LIMIT_SECONDS,
            )
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
    return await call_next(request)


# ---------------------------------------------------------------------------
# Consistent error format: wrap FastAPI default HTTPException detail
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    exc_str = str(exc)
    exc_name = type(exc).__name__

    if (
        "SSL handshake failed" in exc_str
        or "TLSV1_ALERT_INTERNAL_ERROR" in exc_str
        or "ServerSelectionTimeoutError" in exc_name
        or "AutoReconnect" in exc_name
    ):
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Database connection failed: MongoDB Atlas SSL/TLS handshake rejected. "
                    "Your current IP address is not whitelisted in MongoDB Atlas. "
                    "Please log into MongoDB Atlas -> Network Access and add your current IP (or 0.0.0.0/0 to allow all)."
                )
            },
        )

    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {exc_str or exc_name}"},
    )


# ---------------------------------------------------------------------------
# Routers  (catalog registered once – removed duplicate from old main)
# ---------------------------------------------------------------------------
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(logs_router, prefix=settings.API_V1_PREFIX)
app.include_router(recommend_router, prefix=settings.API_V1_PREFIX)
app.include_router(feedback_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(catalog_router, prefix=settings.API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness check",
    response_description="Returns service status",
)
async def health_check():
    """Simple liveness endpoint – returns 200 when server is up."""
    return {"status": "ok", "service": settings.APP_NAME, "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Web Portal & Login UI
# ---------------------------------------------------------------------------
_STATIC_LOGIN_HTML = Path(__file__).resolve().parent / "static" / "login.html"


@app.get("/login", include_in_schema=False)
@app.get("/", include_in_schema=False)
async def serve_login_page():
    """Serves the standalone interactive login & dashboard portal."""
    if _STATIC_LOGIN_HTML.exists():
        return FileResponse(_STATIC_LOGIN_HTML, media_type="text/html")
    return JSONResponse(
        status_code=404,
        content={"detail": "Login portal page not found"},
    )

