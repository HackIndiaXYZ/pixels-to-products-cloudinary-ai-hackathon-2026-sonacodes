"""AI recognition and recommendation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.providers import get_ai_provider
from app.ai.service import get_recommendations_for_request, validate_recognition_payload
from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.errors import AppError
from app.models import ClothingItem, User
from app.schemas import AIRecommendationRequest, AIRecommendationResponse, AIRecognitionRequest, AIRecognitionResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/capabilities")
def ai_capabilities(_user: User = Depends(get_current_user)) -> dict:
    settings = get_settings()
    cloudinary_status = {
        "configured": settings.cloudinary_configured,
        "image_tagging": "available" if settings.cloudinary_configured and settings.cloudinary_enable_image_tagging else "unavailable",
        "background_removal": "available" if settings.cloudinary_configured and settings.cloudinary_enable_background_removal else "unavailable",
        "image_transformations": "available" if settings.cloudinary_configured else "unavailable",
        "layered_composition": "available" if settings.cloudinary_configured else "unavailable",
    }
    return {"cloudinary": cloudinary_status, "external_ai_providers": False}


@router.post("/recognize-clothing", response_model=AIRecognitionResponse)
def recognize_clothing(
    payload: AIRecognitionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIRecognitionResponse:
    item = (
        db.query(ClothingItem)
        .filter(
            ClothingItem.cloudinary_public_id == payload.cloudinary_public_id,
            ClothingItem.user_id == user.id,
        )
        .one_or_none()
    )
    if item is None:
        raise AppError("The clothing item was not found.", status_code=404, code="not_found")
    provider = get_ai_provider()
    raw = provider.recognize_clothing(public_id=item.cloudinary_public_id, secure_url=item.secure_url)
    recognition = validate_recognition_payload(raw)
    return AIRecognitionResponse(success=True, recognition=recognition, provider=getattr(provider, "provider_name", "cloudinary"))


@router.post("/analyse-cloudinary-asset", response_model=AIRecognitionResponse)
def analyse_cloudinary_asset(
    payload: AIRecognitionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIRecognitionResponse:
    return recognize_clothing(payload=payload, user=user, db=db)


@router.post("/recommend-outfits", response_model=AIRecommendationResponse)
def recommend_outfits(
    payload: AIRecommendationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIRecommendationResponse:
    provider = get_ai_provider()
    items = (
        db.query(ClothingItem)
        .filter(ClothingItem.user_id == user.id)
        .order_by(ClothingItem.created_at.desc())
        .all()
    )
    if not items:
        return AIRecommendationResponse(
            success=False,
            recommendations=[],
            warning="Add more wardrobe items before requesting outfit recommendations.",
            provider=getattr(provider, "provider_name", "cloudinary"),
        )

    include = set(payload.include_item_ids or [])
    exclude = set(payload.exclude_item_ids or [])
    if include:
        filtered = [item for item in items if item.id in include]
    else:
        filtered = [item for item in items if item.id not in exclude]
    if not filtered:
        return AIRecommendationResponse(
            success=False,
            recommendations=[],
            warning="No compatible items remain after applying your exclusions.",
            provider=getattr(provider, "provider_name", "cloudinary"),
        )

    if payload.occasion and payload.occasion not in {"Casual", "Office", "University", "Formal event", "Party", "Date", "Wedding", "Travel", "Workout", "Everyday", "Work", "Evening", "Weekend", "Special occasion"}:
        raise AppError("Unsupported occasion for outfit recommendations.", status_code=422, code="validation_error")

    recommendations = get_recommendations_for_request(filtered, payload, provider=provider)
    if not recommendations:
        return AIRecommendationResponse(
            success=False,
            recommendations=[],
            warning="There are not enough compatible wardrobe items for this request. Add a top-and-bottom pairing, a dress, or remove a constraint.",
            provider=getattr(provider, "provider_name", "cloudinary"),
        )

    return AIRecommendationResponse(
        success=True,
        recommendations=recommendations,
        provider=getattr(provider, "provider_name", "cloudinary"),
    )
