"""Service layer for AI model validation and recommendation scoring."""

from __future__ import annotations

from collections.abc import Iterable

from app.ai.providers import CloudinaryProvider
from app.ai.schemas import ClothingRecognition, RecommendationRequest, RecommendationSet
from app.errors import AppError
from app.models import ClothingItem

CATEGORY_ORDER = ["Tops", "Bottoms", "Dresses", "Outerwear", "Shoes", "Accessories", "Bags"]


def validate_recognition_payload(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise AppError("The AI model returned malformed recognition data.", status_code=422, code="ai_invalid_response")
    try:
        payload = ClothingRecognition.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise AppError("The AI model response is missing required clothing attributes.", status_code=422, code="ai_invalid_response") from exc
    return payload.model_dump(exclude_none=True)


def validate_recommendation_payload(raw: object, valid_ids: set[int]) -> list[dict]:
    if not isinstance(raw, dict):
        raise AppError("The AI recommendation response was malformed.", status_code=422, code="ai_invalid_response")
    recommendations = raw.get("recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        raise AppError("The AI recommendation response did not include any outfits.", status_code=422, code="ai_invalid_response")
    try:
        validated = RecommendationSet.model_validate({"recommendations": recommendations})
    except Exception as exc:  # noqa: BLE001
        raise AppError("The AI model returned invalid outfit recommendations.", status_code=422, code="ai_invalid_response") from exc

    cleaned: list[dict] = []
    for rec in validated.recommendations:
        item_ids = rec.item_ids
        invalid = [item_id for item_id in item_ids if item_id not in valid_ids]
        if invalid:
            raise AppError(
                "The AI stylist returned item IDs that are not in the wardrobe candidate set.",
                status_code=422,
                code="ai_invalid_response",
            )
        cleaned.append(
            {
                "title": rec.title,
                "description": rec.description,
                "occasion": rec.occasion,
                "style": rec.style,
                "item_ids": item_ids,
                "styling_tips": rec.styling_tips,
                "reasoning": rec.reasoning,
                "compatibility_score": rec.compatibility_score,
            }
        )
    return cleaned


def build_outfit_candidates(items: Iterable[ClothingItem], payload: RecommendationRequest) -> list[dict]:
    included = {int(item.id) for item in items if int(item.id) not in set(payload.exclude_item_ids or [])}
    if payload.include_item_ids:
        included = {item_id for item_id in included if item_id in set(payload.include_item_ids)}

    tops = [item for item in items if item.category == "Tops" and item.id in included]
    bottoms = [item for item in items if item.category == "Bottoms" and item.id in included]
    dresses = [item for item in items if item.category == "Dresses" and item.id in included]
    shoes = [item for item in items if item.category == "Shoes" and item.id in included]
    outerwear = [item for item in items if item.category == "Outerwear" and item.id in included]
    accessories = [item for item in items if item.category in {"Accessories", "Bags"} and item.id in included]

    options: list[dict] = []
    for dress in dresses:
        outfit = [dress]
        if shoes:
            outfit.append(shoes[0])
        if accessories:
            outfit.append(accessories[0])
        options.append({"item_ids": [item.id for item in outfit], "score": score_outfit(outfit, payload)})

    for top in tops:
        for bottom in bottoms:
            outfit = [top, bottom]
            if shoes:
                outfit.append(shoes[0])
            if outerwear:
                outfit.append(outerwear[0])
            if accessories:
                outfit.append(accessories[0])
            options.append({"item_ids": [item.id for item in outfit], "score": score_outfit(outfit, payload)})

    unique = []
    seen: set[tuple[int, ...]] = set()
    for option in options:
        key = tuple(option["item_ids"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(option)
    unique.sort(key=lambda item: item["score"], reverse=True)
    return unique[:12]


def score_outfit(items: list[ClothingItem], payload: RecommendationRequest) -> float:
    if not items:
        return 0.0
    category_score = 1.0 if any(item.category in {"Tops", "Bottoms", "Dresses", "Shoes"} for item in items) else 0.3
    style_score = 1.0 if not payload.preferred_style else _style_match(items, payload.preferred_style)
    occasion_score = 1.0 if not payload.occasion else _occasion_match(items, payload.occasion)
    colour_score = _colour_score(items, payload.preferred_colours, payload.avoid_colours)
    season_score = _season_score(items, payload.season)
    total = category_score * 25 + style_score * 20 + occasion_score * 20 + colour_score * 20 + season_score * 15
    return max(0.0, min(100.0, total))


def _style_match(items: list[ClothingItem], preferred_style: str) -> float:
    matches = sum(1 for item in items if str(item.style).lower() == preferred_style.lower())
    if not matches:
        return 0.5
    return min(1.0, 0.5 + matches / max(1, len(items) * 2))


def _occasion_match(items: list[ClothingItem], occasion: str) -> float:
    if not occasion:
        return 1.0
    match_count = sum(1 for item in items if str(item.occasion).lower() == occasion.lower())
    if not match_count:
        return 0.6
    return min(1.0, 0.5 + match_count / max(1, len(items)))


def _colour_score(items: list[ClothingItem], preferred_colours: list[str], avoid_colours: list[str]) -> float:
    if not preferred_colours and not avoid_colours:
        return 1.0
    score = 0.5
    for item in items:
        colour = item.colour.lower()
        if any(pref.lower() == colour for pref in preferred_colours):
            score += 0.25
        if any(avoid.lower() == colour for avoid in avoid_colours):
            score -= 0.4
    return max(0.0, min(1.0, score))


def _season_score(items: list[ClothingItem], season: str | None) -> float:
    if not season:
        return 1.0
    matches = sum(1 for item in items if str(item.season or "All seasons").lower() == season.lower() or str(item.season or "All seasons").lower() == "all seasons")
    return min(1.0, 0.5 + matches / max(1, len(items)))


def get_recommendations_for_request(db_items: list[ClothingItem], payload: RecommendationRequest, provider=None) -> list[dict]:
    if not db_items:
        return []
    candidates = build_outfit_candidates(db_items, payload)
    if not candidates:
        return []

    if provider is None:
        raise AppError("AI provider is not configured.", status_code=503, code="ai_not_configured")
    response = provider.recommend_outfits(
        candidate_outfits=[
            {
                "item_ids": item["item_ids"],
                "score": item["score"],
                "items": [
                    {
                        "id": option.id,
                        "name": option.name,
                        "category": option.category,
                        "colour": option.colour,
                        "style": option.style,
                        "occasion": option.occasion,
                    }
                    for option in (next(item_obj for item_obj in db_items if item_obj.id == item_id) for item_id in item["item_ids"])
                ],
            }
            for item in candidates
        ],
        preferences=payload.model_dump(mode="json"),
    )
    valid_ids = {item.id for item in db_items}
    validated = validate_recommendation_payload(response, valid_ids)
    if not validated:
        return []
    final: list[dict] = []
    for rec in validated:
        item_ids = rec["item_ids"]
        items_by_id = {item.id: item for item in db_items}
        ordered = [items_by_id[item_id] for item_id in item_ids if item_id in items_by_id]
        final.append(
            {
                "title": rec["title"],
                "description": rec["description"],
                "occasion": rec["occasion"],
                "style": rec["style"],
                "items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "category": item.category,
                        "colour": item.colour,
                        "secure_url": item.secure_url,
                    }
                    for item in ordered
                ],
                "composition_url": CloudinaryProvider.build_composition_url(ordered),
                "styling_tips": rec["styling_tips"],
                "reasoning": rec["reasoning"],
                "compatibility_score": rec["compatibility_score"],
            }
        )
    seen: set[tuple[int, ...]] = set()
    deduped: list[dict] = []
    for rec in final:
        key = tuple(item["id"] for item in rec["items"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rec)
    return deduped[:3]
