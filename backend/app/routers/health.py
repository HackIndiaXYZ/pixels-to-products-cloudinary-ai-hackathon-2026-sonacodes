from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    settings = get_settings()
    return HealthResponse(
        status="ok",
        database="ok",
        cloudinary_configured=settings.cloudinary_configured,
        cloud_name=(
            settings.cloudinary_cloud_name.strip()
            if settings.cloudinary_configured
            else None
        ),
    )
