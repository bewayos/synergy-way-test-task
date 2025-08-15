from __future__ import annotations


def mask_credit_card(cc_number: str | None) -> str | None:
    """
    Mask credit card number, leaving only last 4 digits visible.

    Example:
        "1234 5678 9012 3456" -> "**** **** **** 3456"
    """
    if not cc_number:
        return None
    digits = "".join(ch for ch in cc_number if ch.isdigit())
    if len(digits) < 4:
        return "****"
    return "**** **** **** " + digits[-4:]
