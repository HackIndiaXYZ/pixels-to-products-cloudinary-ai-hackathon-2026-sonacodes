"""Clothing item queries and writes."""

import logging
import math

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AppError, ConflictError, NotFoundError
from app.models import ClothingItem, utcnow
from app.schemas import ItemCreate, ItemPage, ItemUpdate, WardrobeStats
from app.services.cloudinary_service import destroy_asset, verify_asset

logger = logging.getLogger("wardrobeai.items")


def list_items(
    db: Session,
    *,
    user_id: int,
    q: str | None,
    category: str | None,
    colour: str | None,
    pattern: str | None,
    style: str | None,
    occasion: str | None,
    sort: str,
    page: int,
    page_size: int,
) -> ItemPage:
    query = db.query(ClothingItem).filter(ClothingItem.user_id == user_id)
    query = _apply_filters(
        query,
        q=q,
        category=category,
        colour=colour,
        pattern=pattern,
        style=style,
        occasion=occasion,
    )
    total = query.count()
    pages = max(1, math.ceil(total / page_size)) if total else 0
    query = _apply_sort(query, sort)
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return ItemPage(items=rows, total=total, page=page, page_size=page_size, pages=pages)


def get_item(db: Session, item_id: int, user_id: int) -> ClothingItem:
    item = (
        db.query(ClothingItem)
        .filter(ClothingItem.id == item_id, ClothingItem.user_id == user_id)
        .one_or_none()
    )
    if item is None:
        raise NotFoundError()
    return item


def create_item(db: Session, payload: ItemCreate, user_id: int) -> ClothingItem:
    asset = verify_asset(payload.cloudinary_public_id, user_id)
    item = ClothingItem(
        user_id=user_id,
        name=payload.name,
        category=payload.category,
        subcategory=payload.subcategory,
        colour=payload.colour,
        secondary_colour=payload.secondary_colour,
        pattern=payload.pattern,
        style=payload.style,
        occasion=payload.occasion,
        season=payload.season,
        brand=payload.brand,
        notes=payload.notes,
        material=payload.material,
        texture=payload.texture,
        sleeve_type=payload.sleeve_type,
        neckline=payload.neckline,
        fit=payload.fit,
        length=payload.length,
        formality=payload.formality,
        ai_description=payload.ai_description,
        ai_tags=payload.ai_tags,
        recognition_confidence=payload.recognition_confidence,
        recognition_provider=payload.recognition_provider,
        recognition_status=payload.recognition_status,
        cloudinary_public_id=asset.public_id,
        secure_url=asset.secure_url,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.info("Duplicate Cloudinary asset rejected: %s", asset.public_id)
        raise ConflictError("This image is already in the wardrobe.") from exc
    db.refresh(item)
    logger.info("Saved clothing item %s (%s)", item.id, item.cloudinary_public_id)
    return item


def update_item(db: Session, item_id: int, payload: ItemUpdate, user_id: int) -> ClothingItem:
    item = get_item(db, item_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(item, field, value)
    item.updated_at = utcnow()
    db.commit()
    db.refresh(item)
    logger.info("Updated clothing item %s", item.id)
    return item


def delete_item(db: Session, item_id: int, user_id: int) -> None:
    """Delete Cloudinary first, then the database row. See cloudinary_service."""
    item = get_item(db, item_id, user_id)
    public_id = item.cloudinary_public_id
    destroy_asset(public_id, user_id)
    try:
        db.delete(item)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Database delete failed after Cloudinary asset %s was removed",
            public_id,
        )
        raise AppError(
            "The image was removed from Cloudinary, but the wardrobe record could not be deleted. Refresh and try again.",
            status_code=500,
            code="delete_failed",
        ) from exc
    logger.info("Deleted clothing item %s", item_id)


def discard_upload(db: Session, public_id: str, user_id: int) -> None:
    """Remove an uploaded asset that was never saved as a clothing item."""
    from app.services.cloudinary_service import user_upload_folder

    if not public_id.startswith(f"{user_upload_folder(user_id)}/"):
        raise NotFoundError()
    existing = (
        db.query(ClothingItem)
        .filter(ClothingItem.cloudinary_public_id == public_id)
        .one_or_none()
    )
    if existing is not None:
        if existing.user_id != user_id:
            raise NotFoundError()
        raise ConflictError("This image is already saved in the wardrobe.")
    destroy_asset(public_id, user_id)


def wardrobe_stats(db: Session, user_id: int) -> WardrobeStats:
    owned = ClothingItem.user_id == user_id
    total = db.query(func.count(ClothingItem.id)).filter(owned).scalar() or 0
    category_count = (
        db.query(func.count(func.distinct(ClothingItem.category))).filter(owned).scalar() or 0
    )
    top = (
        db.query(ClothingItem.category, func.count(ClothingItem.id))
        .filter(owned)
        .group_by(ClothingItem.category)
        .order_by(func.count(ClothingItem.id).desc(), ClothingItem.category.asc())
        .first()
    )
    recent = (
        db.query(ClothingItem)
        .filter(owned)
        .order_by(ClothingItem.created_at.desc(), ClothingItem.id.desc())
        .limit(4)
        .all()
    )
    colour_rows = (
        db.query(ClothingItem.colour)
        .filter(owned)
        .distinct()
        .order_by(func.lower(ClothingItem.colour).asc())
        .all()
    )
    return WardrobeStats(
        total_items=total,
        category_count=category_count,
        top_category=top[0] if top else None,
        top_category_count=int(top[1]) if top else 0,
        recent_items=recent,
        colours=[row[0] for row in colour_rows if row[0]],
    )


def _apply_filters(query, *, q, category, colour, pattern, style, occasion):
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                ClothingItem.name.ilike(term),
                ClothingItem.colour.ilike(term),
                ClothingItem.brand.ilike(term),
            )
        )
    if category:
        query = query.filter(ClothingItem.category == category)
    if colour:
        query = query.filter(func.lower(ClothingItem.colour) == colour.strip().lower())
    if pattern:
        query = query.filter(ClothingItem.pattern == pattern)
    if style:
        query = query.filter(ClothingItem.style == style)
    if occasion:
        query = query.filter(ClothingItem.occasion == occasion)
    return query


def _apply_sort(query, sort: str):
    if sort == "oldest":
        return query.order_by(ClothingItem.created_at.asc(), ClothingItem.id.asc())
    if sort == "name":
        return query.order_by(func.lower(ClothingItem.name).asc(), ClothingItem.id.asc())
    return query.order_by(ClothingItem.created_at.desc(), ClothingItem.id.desc())
