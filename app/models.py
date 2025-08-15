from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class TimestampMixin:
    """
    Common created/updated timestamps.

    Stored in UTC. `updated_at` is set via SQLAlchemy on each update.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int] = mapped_column(nullable=False, unique=True, index=True)

    name: Mapped[Optional[str]] = mapped_column(String(200))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    company_name: Mapped[Optional[str]] = mapped_column(String(255))

    # One-to-one relationships (uselist=False)
    address: Mapped[Optional[Address]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    credit_card: Mapped[Optional[CreditCard]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"User(id={self.id!r}, external_id={self.external_id!r}, email={self.email!r})"


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"
    __table_args__ = (UniqueConstraint("user_id", name="uq_addresses_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    street: Mapped[Optional[str]] = mapped_column(String(255))
    street_name: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(255))
    state: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(255))
    zip: Mapped[Optional[str]] = mapped_column(String(50))

    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)

    # Keep raw payload for traceability/debugging
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="address")


class CreditCard(Base, TimestampMixin):
    __tablename__ = "credit_cards"
    __table_args__ = (UniqueConstraint("user_id", name="uq_credit_cards_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    cc_number: Mapped[Optional[str]] = mapped_column(String(32))
    cc_type: Mapped[Optional[str]] = mapped_column(String(50))
    exp_month: Mapped[Optional[int]] = mapped_column()
    exp_year: Mapped[Optional[int]] = mapped_column()

    raw_json: Mapped[Optional[dict]] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="credit_card")
