from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_name: Optional[str] = None


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    street: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class CreditCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    # Note: API layer will mask/transform sensitive `cc_number` before sending to clients.
    cc_number: Optional[str] = None
    cc_type: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None


class UserOut(UserBase):
    address: Optional[AddressOut] = None
    credit_card: Optional[CreditCardOut] = None
