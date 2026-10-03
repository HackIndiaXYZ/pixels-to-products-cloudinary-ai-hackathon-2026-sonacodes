from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import CATEGORIES, OCCASIONS, PATTERNS, SORTS, STYLES
from app.database import get_db
from app.dependencies import get_current_user, require_csrf
from app.errors import AppError
from app.models import User
from app.schemas import ItemCreate, ItemPage, ItemRead, ItemUpdate
from app.services import item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ItemPage)
def list_items(
    q: str | None = Query(default=None, max_length=80),
    category: str | None = Query(default=None),
    colour: str | None = Query(default=None, max_length=40),
    pattern: str | None = Query(default=None),
    style: str | None = Query(default=None),
    occasion: str | None = Query(default=None),
    sort: str = Query(default="recent"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=60),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemPage:
    if category and category not in CATEGORIES:
        raise AppError("Unknown category.", status_code=422, code="validation_error")
    if pattern and pattern not in PATTERNS:
        raise AppError("Unknown pattern.", status_code=422, code="validation_error")
    if style and style not in STYLES:
        raise AppError("Unknown style.", status_code=422, code="validation_error")
    if occasion and occasion not in OCCASIONS:
        raise AppError("Unknown occasion.", status_code=422, code="validation_error")
    if sort not in SORTS:
        raise AppError("Unknown sort.", status_code=422, code="validation_error")
    return item_service.list_items(
        db,
        user_id=user.id,
        q=q,
        category=category,
        colour=colour,
        pattern=pattern,
        style=style,
        occasion=occasion,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ItemRead, status_code=201)
def create_item(
    payload: ItemCreate,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> ItemRead:
    return item_service.create_item(db, payload, user.id)


@router.get("/{item_id}", response_model=ItemRead)
def get_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemRead:
    return item_service.get_item(db, item_id, user.id)


@router.put("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> ItemRead:
    return item_service.update_item(db, item_id, payload, user.id)


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> None:
    item_service.delete_item(db, item_id, user.id)
