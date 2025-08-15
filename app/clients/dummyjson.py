from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


@dataclass
class DummyJSONConfig:
    base_url: str
    timeout: int


class DummyJSONClient:
    """
    Minimal HTTP client for DummyJSON users API.

    Docs: https://dummyjson.com/docs/users
    """

    def __init__(self, config: DummyJSONConfig) -> None:
        self._base = config.base_url.rstrip("/")
        self._timeout = config.timeout

    @classmethod
    def from_settings(cls, settings: Any) -> "DummyJSONClient":
        return cls(
            DummyJSONConfig(
                base_url=settings.dummyjson_base_url,
                timeout=int(settings.request_timeout_seconds),
            )
        )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self._base}/{path.lstrip('/')}"
        resp = requests.get(url, params=params or {}, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    # -------- API methods --------

    def list_users(self, *, limit: int = 100, skip: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        Returns (users, total). Supports pagination via limit/skip.
        """
        payload = self._get("users", params={"limit": limit, "skip": skip})
        users: List[Dict[str, Any]] = payload.get("users", []) or []
        total: int = int(payload.get("total", len(users)))
        return users, total

    def get_user(self, external_id: int) -> Dict[str, Any]:
        return self._get(f"users/{external_id}")

    # -------- Mapping helpers (DummyJSON -> internal dicts for models) --------

    @staticmethod
    def map_user(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map DummyJSON user to our User model fields.
        """
        first = (user.get("firstName") or "").strip()
        last = (user.get("lastName") or "").strip()
        full_name = " ".join([p for p in (first, last) if p]).strip() or None

        company = (user.get("company") or {}) or {}
        return {
            "external_id": int(user["id"]),
            "name": full_name,
            "username": user.get("username"),
            "email": user.get("email"),
            "phone": user.get("phone"),
            "website": user.get("domain"),
            "company_name": company.get("name"),
        }

    @staticmethod
    def map_address(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map DummyJSON user.address to our Address model fields.
        """
        addr = (user.get("address") or {}) or {}
        coords = (addr.get("coordinates") or {}) or {}
        return {
            "street": addr.get("address"),
            "street_name": None,  # DummyJSON has no distinct street_name
            "city": addr.get("city"),
            "state": addr.get("state"),
            "country": addr.get("country"),
            "zip": addr.get("postalCode"),
            "lat": _safe_float(coords.get("lat")),
            "lng": _safe_float(coords.get("lng")),
            "raw_json": addr,
        }

    @staticmethod
    def map_credit_card(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map DummyJSON user.bank to our CreditCard model fields.
        """
        bank = (user.get("bank") or {}) or {}
        exp_month, exp_year = _parse_mm_yy(bank.get("cardExpire"))
        return {
            "cc_number": bank.get("cardNumber"),
            "cc_type": bank.get("cardType"),
            "exp_month": exp_month,
            "exp_year": exp_year,
            "raw_json": bank,
        }


def _parse_mm_yy(value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse 'MM/YY' into (month, year), year normalized to 2000+YY.
    """
    if not value or "/" not in value:
        return None, None
    try:
        mm_str, yy_str = value.split("/", 1)
        mm = int(mm_str)
        yy = int(yy_str)
        if not (1 <= mm <= 12):
            return None, None
        # Normalize to 2000+YY
        return mm, 2000 + yy
    except Exception:
        return None, None


def _safe_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None
