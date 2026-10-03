from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import WardrobeStats
from app.services.item_service import wardrobe_stats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=WardrobeStats)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> WardrobeStats:
    return wardrobe_stats(db, user.id)
