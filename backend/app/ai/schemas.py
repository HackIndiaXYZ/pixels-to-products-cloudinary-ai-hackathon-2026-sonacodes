"""Validated AI response contracts for recognition and styling."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["Tops", "Bottoms", "Dresses", "Outerwear", "Shoes", "Accessories", "Bags"]
Pattern = Literal[
    "Solid",
    "Striped",
    "Checked",
    "Floral",
    "Polka dot",
    "Graphic",
    "Textured",
    "Animal print",
    "Other",
]


class RecognitionConfidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: float | None = None
    primary_colour: float | None = None
    pattern: float | None = None
    material: float | None = None
    texture: float | None = None
    sleeve_type: float | None = None
    neckline: float | None = None
    fit: float | None = None
    length: float | None = None
    style: float | None = None
    formality: float | None = None

    @field_validator(
        "category",
        "primary_colour",
        "pattern",
        "material",
        "texture",
        "sleeve_type",
        "neckline",
        "fit",
        "length",
        "style",
        "formality",
    )
    @classmethod
    def ensure_score_range(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if not 0 <= value <= 1:
            raise ValueError("Confidence scores must be between 0 and 1.")
        return value


class ClothingRecognition(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_name: str = Field(min_length=1)
    category: Category
    subcategory: str | None = None
    primary_colour: str | None = None
    secondary_colour: str | None = None
    pattern: Pattern | str = "Solid"
    material: str | None = None
    texture: str | None = None
    sleeve_type: str | None = None
    neckline: str | None = None
    fit: str | None = None
    length: str | None = None
    style: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)
    formality: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    recognition_source: str | None = "cloudinary"
    recognition_status: str | None = "completed"
    confidence: RecognitionConfidence = Field(default_factory=RecognitionConfidence)

    @field_validator("item_name", "primary_colour", "secondary_colour", "material", "texture", "sleeve_type", "neckline", "fit", "length", "formality", "description")
    @classmethod
    def normalise_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("style", "occasions", "seasons", "tags")
    @classmethod
    def normalise_list(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]


class OutfitRecommendationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    occasion: str = Field(min_length=1)
    style: str = Field(min_length=1)
    item_ids: list[int]
    styling_tips: list[str] = Field(default_factory=list)
    reasoning: str = Field(min_length=1)
    compatibility_score: float

    @field_validator("item_ids")
    @classmethod
    def ensure_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("At least one wardrobe item is required.")
        return value

    @field_validator("compatibility_score")
    @classmethod
    def ensure_score(cls, value: float) -> float:
        if not 0 <= float(value) <= 100:
            raise ValueError("Compatibility score must be between 0 and 100.")
        return float(value)


class RecommendationSet(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recommendations: list[OutfitRecommendationResult]


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    occasion: str | None = None
    preferred_style: str | None = None
    preferred_colours: list[str] = Field(default_factory=list)
    avoid_colours: list[str] = Field(default_factory=list)
    season: str | None = None
    weather: dict | None = None
    include_item_ids: list[int] = Field(default_factory=list)
    exclude_item_ids: list[int] = Field(default_factory=list)

    @field_validator("preferred_colours", "avoid_colours")
    @classmethod
    def clean_colours(cls, value: list[str]) -> list[str]:
        return [str(item).strip() for item in value if str(item).strip()]
