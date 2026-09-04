from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, unhandled_exception_handler
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Foundation API for the AI-Powered Border Checkpoint & Travel Document "
        "Verification Platform. Phase 1: authentication, RBAC, users, and "
        "checkpoints only. AI modules (OCR, MRZ, face verification, tamper "
        "detection, risk engine) are added in later phases."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("%s starting up in '%s' environment", settings.APP_NAME, settings.ENVIRONMENT)


@app.get("/")
def root() -> dict:
    return {"service": settings.APP_NAME, "status": "running", "docs": "/docs"}
