"""WardrobeAI API entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.errors import AppError
from app.routers import ai, auth, health, items, stats, uploads

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("wardrobeai")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    settings = get_settings()
    logger.info(
        "WardrobeAI API ready (cloudinary_configured=%s)",
        settings.cloudinary_configured,
    )
    yield


app = FastAPI(title="WardrobeAI", version="1.0.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        key = ".".join(location) or "request"
        fields[key] = error.get("msg", "Invalid value.")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Check the highlighted fields and try again.",
                "fields": fields,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Something went wrong. Please try again.",
            }
        },
    )
