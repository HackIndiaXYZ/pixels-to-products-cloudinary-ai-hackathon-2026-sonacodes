"""Request and response schemas for the wardrobe API."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Category = Literal[
    "Tops", "Bottoms", "Dresses", "Outerwear", "Shoes", "Accessories", "Bags"
]
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
Style = Literal[
    "Casual",
    "Smart casual",
    "Formal",
    "Minimal",
    "Classic",
    "Sporty",
    "Bohemian",
    "Streetwear",
]
Occasion = Literal["Everyday", "Work", "Evening", "Weekend", "Travel", "Special occasion"]
Season = Literal["Spring", "Summer", "Autumn", "Winter", "All seasons"]
Sort = Literal["recent", "oldest", "name"]

PUBLIC_ID_RE = re.compile(r"^wardrobeai/users/[1-9][0-9]*/clothing/[A-Za-z0-9][A-Za-z0-9_\-/]{0,200}$")


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("This field is required.")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=80)
    category: Category
    subcategory: str | None = Field(default=None, max_length=80)
    colour: str = Field(min_length=1, max_length=40)
    secondary_colour: str | None = Field(default=None, max_length=40)
    pattern: Pattern
    style: Style
    occasion: Occasion
    season: Season | None = None
    brand: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)
    material: str | None = Field(default=None, max_length=80)
    texture: str | None = Field(default=None, max_length=80)
    sleeve_type: str | None = Field(default=None, max_length=80)
    neckline: str | None = Field(default=None, max_length=80)
    fit: str | None = Field(default=None, max_length=80)
    length: str | None = Field(default=None, max_length=80)
    formality: str | None = Field(default=None, max_length=80)
    ai_description: str | None = Field(default=None, max_length=2000)
    ai_tags: str | None = Field(default=None, max_length=500)
    recognition_confidence: float | None = None
    recognition_provider: str | None = Field(default=None, max_length=40)
    recognition_status: str | None = Field(default=None, max_length=40)
    cloudinary_public_id: str = Field(min_length=1, max_length=255)

    @field_validator("name", "colour")
    @classmethod
    def required_text(cls, value: str) -> str:
        return _clean_required(value)

    @field_validator(
        "subcategory",
        "secondary_colour",
        "brand",
        "notes",
        "material",
        "texture",
        "sleeve_type",
        "neckline",
        "fit",
        "length",
        "formality",
        "ai_description",
        "ai_tags",
        "recognition_provider",
        "recognition_status",
    )
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return _clean_optional(value)

    @field_validator("cloudinary_public_id")
    @classmethod
    def public_id_in_folder(cls, value: str) -> str:
        cleaned = value.strip()
        if not PUBLIC_ID_RE.match(cleaned):
            raise ValueError("Image identifier is not a WardrobeAI Cloudinary asset.")
        return cleaned


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, max_length=80)
    category: Category | None = None
    subcategory: str | None = Field(default=None, max_length=80)
    colour: str | None = Field(default=None, max_length=40)
    secondary_colour: str | None = Field(default=None, max_length=40)
    pattern: Pattern | None = None
    style: Style | None = None
    occasion: Occasion | None = None
    season: Season | None = None
    brand: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)
    material: str | None = Field(default=None, max_length=80)
    texture: str | None = Field(default=None, max_length=80)
    sleeve_type: str | None = Field(default=None, max_length=80)
    neckline: str | None = Field(default=None, max_length=80)
    fit: str | None = Field(default=None, max_length=80)
    length: str | None = Field(default=None, max_length=80)
    formality: str | None = Field(default=None, max_length=80)
    ai_description: str | None = Field(default=None, max_length=2000)
    ai_tags: str | None = Field(default=None, max_length=500)
    recognition_confidence: float | None = None
    recognition_provider: str | None = Field(default=None, max_length=40)
    recognition_status: str | None = Field(default=None, max_length=40)

    @field_validator("name", "colour")
    @classmethod
    def required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_required(value)

    @field_validator(
        "subcategory",
        "secondary_colour",
        "brand",
        "notes",
        "material",
        "texture",
        "sleeve_type",
        "neckline",
        "fit",
        "length",
        "formality",
        "ai_description",
        "ai_tags",
        "recognition_provider",
        "recognition_status",
    )
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return _clean_optional(value)


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    subcategory: str | None
    colour: str
    secondary_colour: str | None
    pattern: str
    style: str
    occasion: str
    season: str | None
    brand: str | None
    notes: str | None
    material: str | None = None
    texture: str | None = None
    sleeve_type: str | None = None
    neckline: str | None = None
    fit: str | None = None
    length: str | None = None
    formality: str | None = None
    ai_description: str | None = None
    ai_tags: str | None = None
    recognition_confidence: float | None = None
    recognition_provider: str | None = None
    recognition_status: str | None = None
    cloudinary_public_id: str
    secure_url: str
    created_at: datetime
    updated_at: datetime


class ItemPage(BaseModel):
    items: list[ItemRead]
    total: int
    page: int
    page_size: int
    pages: int


class WardrobeStats(BaseModel):
    total_items: int
    category_count: int
    top_category: str | None
    top_category_count: int
    recent_items: list[ItemRead]
    colours: list[str]


class AIRecognitionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cloudinary_public_id: str = Field(min_length=1, max_length=255)
    secure_url: str = Field(min_length=1, max_length=1000)


class AIRecognitionResponse(BaseModel):
    success: bool
    recognition: dict
    provider: str


class AIRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    occasion: str | None = None
    preferred_style: str | None = None
    preferred_colours: list[str] = Field(default_factory=list)
    avoid_colours: list[str] = Field(default_factory=list)
    season: str | None = None
    weather: dict | None = None
    include_item_ids: list[int] = Field(default_factory=list)
    exclude_item_ids: list[int] = Field(default_factory=list)


class AIRecommendationResponse(BaseModel):
    success: bool
    recommendations: list[dict]
    provider: str | None = None
    warning: str | None = None


class SignatureResponse(BaseModel):
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    allowed_formats: str
    upload_url: str


class DiscardUpload(BaseModel):
    public_id: str = Field(min_length=1, max_length=255)

    @field_validator("public_id")
    @classmethod
    def public_id_in_folder(cls, value: str) -> str:
        cleaned = value.strip()
        if not PUBLIC_ID_RE.match(cleaned):
            raise ValueError("Image identifier is not a WardrobeAI Cloudinary asset.")
        return cleaned


class HealthResponse(BaseModel):
    status: str
    database: str
    cloudinary_configured: bool
    cloud_name: str | None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=1, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Full name is required.")
        return cleaned

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        categories = sum((
            any(char.islower() for char in value),
            any(char.isupper() for char in value),
            any(char.isdigit() for char in value),
            any(not char.isalnum() for char in value),
        ))
        if categories < 3:
            raise ValueError("Use at least three of lowercase, uppercase, number, and symbol.")
        return value

    @model_validator(mode="after")
    def matching_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    user: UserRead
    csrf_token: str


class CSRFResponse(BaseModel):
    csrf_token: str


class ErrorBody(BaseModel):
    code: str
    message: str
    fields: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
