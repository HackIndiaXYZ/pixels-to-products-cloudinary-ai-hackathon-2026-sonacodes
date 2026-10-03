"""Clothing item persistence. Optional text fields leave room for later AI attributes."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClothingItem(Base):
    __tablename__ = "clothing_items"
    __table_args__ = (
        Index("ix_clothing_items_category", "category"),
        Index("ix_clothing_items_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(80), nullable=True)
    colour: Mapped[str] = mapped_column(String(40), nullable=False)
    secondary_colour: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pattern: Mapped[str] = mapped_column(String(40), nullable=False)
    style: Mapped[str] = mapped_column(String(40), nullable=False)
    occasion: Mapped[str] = mapped_column(String(40), nullable=False)
    season: Mapped[str | None] = mapped_column(String(40), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    material: Mapped[str | None] = mapped_column(String(80), nullable=True)
    texture: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sleeve_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    neckline: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fit: Mapped[str | None] = mapped_column(String(80), nullable=True)
    length: Mapped[str | None] = mapped_column(String(80), nullable=True)
    formality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    recognition_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recognition_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    recognition_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    secure_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_user_expires", "user_id", "expires_at"),)

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
