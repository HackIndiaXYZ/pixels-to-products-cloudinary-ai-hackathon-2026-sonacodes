"""Cloudinary-first AI provider for wardrobe recognition and recommendations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import cloudinary
import cloudinary.api

from app.config import get_settings
from app.errors import AppError

logger = logging.getLogger("wardrobeai.ai")

CATEGORY_ALIASES = {
    "shirt": "Tops",
    "top": "Tops",
    "blouse": "Tops",
    "tee": "Tops",
    "tshirt": "Tops",
    "sweater": "Tops",
    "sweatshirt": "Tops",
    "hoodie": "Tops",
    "trouser": "Bottoms",
    "pants": "Bottoms",
    "jeans": "Bottoms",
    "skirt": "Bottoms",
    "dress": "Dresses",
    "coat": "Outerwear",
    "jacket": "Outerwear",
    "blazer": "Outerwear",
    "sneaker": "Shoes",
    "shoe": "Shoes",
    "boots": "Shoes",
    "heels": "Shoes",
    "bag": "Bags",
    "handbag": "Bags",
    "purse": "Bags",
    "belt": "Accessories",
    "scarf": "Accessories",
    "hat": "Accessories",
}

COLOUR_ALIASES = {
    "ivory": "Ivory",
    "white": "White",
    "beige": "Beige",
    "cream": "Cream",
    "black": "Black",
    "charcoal": "Charcoal",
    "grey": "Grey",
    "gray": "Grey",
    "navy": "Navy",
    "blue": "Blue",
    "denim": "Blue",
    "brown": "Brown",
    "camel": "Camel",
    "tan": "Tan",
    "olive": "Olive",
    "green": "Green",
    "red": "Red",
    "maroon": "Maroon",
    "pink": "Pink",
    "purple": "Purple",
    "yellow": "Yellow",
    "orange": "Orange",
    "silver": "Silver",
    "gold": "Gold",
    "multicolour": "Multicolour",
    "multicolor": "Multicolour",
}

PATTERN_ALIASES = {
    "solid": "Solid",
    "plain": "Solid",
    "stripe": "Striped",
    "striped": "Striped",
    "checked": "Checked",
    "plaid": "Checked",
    "floral": "Floral",
    "flower": "Floral",
    "flowerprint": "Floral",
    "polka": "Polka dot",
    "dot": "Polka dot",
    "graphic": "Graphic",
    "print": "Graphic",
    "textured": "Textured",
    "animal": "Animal print",
    "leopard": "Animal print",
    "zebra": "Animal print",
}


class AIProvider(ABC):
    provider_name = "base"

    @abstractmethod
    def recognize_clothing(self, *, public_id: str, secure_url: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def recommend_outfits(self, *, candidate_outfits: list[dict], preferences: dict) -> dict:
        raise NotImplementedError


class CloudinaryProvider(AIProvider):
    provider_name = "cloudinary"

    @staticmethod
    def build_composition_url(items: list[object]) -> str:
        settings = get_settings()
        if not settings.cloudinary_configured:
            return ""
        cloud_name = settings.cloudinary_cloud_name.strip()
        if not cloud_name or not items:
            return ""
        base = f"https://res.cloudinary.com/{cloud_name}/image/upload/"
        transforms = ["c_pad,w_800,h_420,b_rgb:f3eee7"]
        positions = [
            (0, 0, 220, 220),
            (240, 30, 240, 240),
            (500, 70, 200, 200),
        ]
        for index, item in enumerate(items[:3]):
            public_id = str(getattr(item, "cloudinary_public_id", "") or "").strip()
            if not public_id:
                continue
            x, y, width, height = positions[index] if index < len(positions) else (0, 0, 180, 180)
            layer_id = public_id.replace("/", ":")
            transforms.extend(
                [
                    f"l_{layer_id},w_{width},h_{height},c_pad,g_center,bo_1px_solid_white,x_{x},y_{y}",
                    "fl_layer_apply",
                ]
            )
        base_id = str(getattr(items[0], "cloudinary_public_id", "") or "").strip()
        if not base_id or len(transforms) == 1:
            return ""
        return base + "/".join(transforms + [base_id])

    def _configure(self) -> None:
        settings = get_settings()
        if not settings.cloudinary_configured:
            raise AppError(
                "Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to backend/.env.",
                status_code=503,
                code="cloudinary_not_configured",
            )
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name.strip(),
            api_key=settings.cloudinary_api_key.strip(),
            api_secret=settings.cloudinary_api_secret.strip(),
            secure=True,
        )

    @staticmethod
    def _normalise_text(value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _normalise_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            items = value
        elif isinstance(value, str):
            items = [value]
        else:
            items = [value]
        cleaned: list[str] = []
        for item in items:
            text = CloudinaryProvider._normalise_text(item)
            if text:
                cleaned.append(text)
        return cleaned

    def _fetch_asset_metadata(self, public_id: str) -> dict:
        self._configure()
        try:
            return cloudinary.api.resource(public_id, resource_type="image", colors=True, faces=True, image_metadata=True)
        except Exception as exc:  # pragma: no cover - runtime fallback for unanalysed assets
            logger.info("Cloudinary asset metadata unavailable for %s: %s", public_id, exc)
            return {}

    @staticmethod
    def _infer_colour_name(colour_value: object) -> str | None:
        if colour_value is None:
            return None
        if isinstance(colour_value, dict):
            candidate = colour_value.get("color") or colour_value.get("name") or colour_value.get("hex")
            colour = str(candidate or "").strip()
        else:
            colour = str(colour_value).strip()
        if not colour:
            return None
        lower = colour.lower().replace("#", "")
        for key, value in COLOUR_ALIASES.items():
            if lower in {key, value.lower()}:
                return value
        if lower.startswith("rgba"):
            return "Multicolour"
        return colour.title()

    @classmethod
    def _infer_category(cls, tags: list[str]) -> str:
        haystack = " ".join(tag.lower() for tag in tags)
        for token, category in CATEGORY_ALIASES.items():
            if token in haystack:
                return category
        if any(keyword in haystack for keyword in ["dress", "gown", "skirt", "trouser", "jacket", "shoe", "bag", "belt", "hat"]):
            return "Tops"
        return "Tops"

    @classmethod
    def _infer_pattern(cls, tags: list[str]) -> str:
        haystack = " ".join(tag.lower() for tag in tags)
        for token, pattern in PATTERN_ALIASES.items():
            if token in haystack:
                return pattern
        return "Solid"

    def _build_title(self, items: list[dict], preferences: dict) -> str:
        primary = items[0].get("name") if items else "Wardrobe pick"
        occasion = preferences.get("occasion") or "Everyday"
        if len(items) == 1:
            return f"{primary} spotlight"
        return f"{occasion} {primary} combination"

    @staticmethod
    def _style_from_items(items: list[dict]) -> str:
        if not items:
            return "Casual"
        styles = [str(item.get("style") or "").strip() for item in items if str(item.get("style") or "").strip()]
        if not styles:
            return "Casual"
        return styles[0]

    @staticmethod
    def _explain_reasoning(items: list[dict], preferences: dict) -> str:
        colours = [str(item.get("colour") or "").strip() for item in items if str(item.get("colour") or "").strip()]
        if len(colours) >= 2:
            if colours[0].lower() == colours[1].lower():
                return "The selected pieces share a coherent colour story, keeping the look balanced and easy to style."
            return "The colour combination blends contrast and harmony, creating a balanced outfit suitable for the selected setting."
        return "The outfit brings together wardrobe staples with compatible styling cues for the selected occasion."

    @staticmethod
    def _styling_tips(items: list[dict], preferences: dict) -> list[str]:
        tips: list[str] = []
        if items:
            first = items[0]
            if first.get("category") == "Tops":
                tips.append("Tuck or layer the top to define the silhouette.")
        if preferences.get("preferred_colours"):
            tips.append("Keep the palette anchored around your preferred colour notes for a cohesive outfit.")
        if not tips:
            tips.append("Add one simple accessory to finish the look without increasing visual noise.")
        return tips[:3]

    def recognize_clothing(self, *, public_id: str, secure_url: str) -> dict:
        info = self._fetch_asset_metadata(public_id)
        tags = self._normalise_list(info.get("tags"))
        contexts = []
        context_value = info.get("context")
        if isinstance(context_value, dict):
            contexts.extend(self._normalise_list(list(context_value.values())))
        elif isinstance(context_value, list):
            contexts.extend(self._normalise_list(context_value))
        all_tags = list(dict.fromkeys(tags + contexts))

        category = self._infer_category(all_tags)
        primary_colour = self._infer_colour_name((info.get("colors") or [{}])[0]) if info.get("colors") else None
        if primary_colour is None and all_tags:
            for tag in all_tags:
                token = tag.lower()
                if token in COLOUR_ALIASES:
                    primary_colour = COLOUR_ALIASES[token]
                    break
        pattern = self._infer_pattern(all_tags)

        item_name = public_id.rsplit("/", 1)[-1].replace("-", " ").title()
        if not item_name:
            item_name = "Wardrobe item"
        description = f"{primary_colour or 'Neutral'} {pattern.lower()} item detected from the uploaded Cloudinary asset."
        confidence = {
            "category": 0.7 if category else None,
            "primary_colour": 0.8 if primary_colour else None,
            "pattern": 0.7 if pattern else None,
        }

        return {
            "item_name": item_name,
            "category": category,
            "subcategory": None,
            "primary_colour": primary_colour,
            "secondary_colour": None,
            "pattern": pattern,
            "material": None,
            "texture": None,
            "sleeve_type": None,
            "neckline": None,
            "fit": None,
            "length": None,
            "style": ["Smart casual"],
            "occasions": ["Everyday"],
            "seasons": ["All seasons"],
            "formality": None,
            "description": description,
            "tags": all_tags[:8],
            "recognition_source": "cloudinary",
            "recognition_status": "completed",
            "confidence": confidence,
        }

    def recommend_outfits(self, *, candidate_outfits: list[dict], preferences: dict) -> dict:
        selected = []
        for outfit in sorted(candidate_outfits or [], key=lambda item: float(item.get("score", 0.0)), reverse=True)[:3]:
            item_ids = outfit.get("item_ids") or []
            items = outfit.get("items") or []
            if not item_ids:
                continue
            occasion = str(preferences.get("occasion") or "Everyday")
            style = str(preferences.get("preferred_style") or self._style_from_items(items) or "Casual")
            title = self._build_title(items, preferences)
            description = f"{occasion} styling built around a balanced {style.lower()} palette."
            score = max(0.0, min(100.0, float(outfit.get("score", 0.0))))
            selected.append(
                {
                    "title": title,
                    "description": description,
                    "occasion": occasion,
                    "style": style,
                    "item_ids": [int(item_id) for item_id in item_ids],
                    "styling_tips": self._styling_tips(items, preferences),
                    "reasoning": self._explain_reasoning(items, preferences),
                    "compatibility_score": round(score, 2),
                }
            )
        return {"recommendations": selected}


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if not settings.cloudinary_configured:
        raise AppError(
            "Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to backend/.env.",
            status_code=503,
            code="cloudinary_not_configured",
        )
    return CloudinaryProvider()
