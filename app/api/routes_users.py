from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Address, CreditCard, User
from app.schemas import UserOut
from app.utils.masking import mask_credit_card

router = APIRouter(prefix="/users", tags=["users"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[UserOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    has_address: bool | None = Query(None),
    has_card: bool | None = Query(None),
):
    """
    List users with optional filters and pagination.
    """
    stmt = select(User).offset(offset).limit(limit)

    if has_address is True:
        stmt = stmt.join(Address).filter(Address.id.isnot(None))
    elif has_address is False:
        stmt = stmt.outerjoin(Address).filter(Address.id.is_(None))

    if has_card is True:
        stmt = stmt.join(CreditCard).filter(CreditCard.id.isnot(None))
    elif has_card is False:
        stmt = stmt.outerjoin(CreditCard).filter(CreditCard.id.is_(None))

    users = db.execute(stmt).scalars().all()

    results: list[UserOut] = []
    for u in users:
        schema = UserOut.model_validate(u)
        if schema.credit_card and schema.credit_card.cc_number:
            schema.credit_card.cc_number = mask_credit_card(schema.credit_card.cc_number)
        results.append(schema)
    return results


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    """
    Get a single user by internal ID.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    schema = UserOut.model_validate(user)
    if schema.credit_card and schema.credit_card.cc_number:
        schema.credit_card.cc_number = mask_credit_card(schema.credit_card.cc_number)
    return schema


@router.get("/ui", response_class=HTMLResponse)
def ui_list_users(db: Annotated[Session, Depends(get_db)]):
    """
    Minimal HTML page to browse saved users.
    """
    users = db.query(User).all()
    html = ["<html><body><h1>Users</h1><ul>"]
    for u in users:
        html.append(f"<li>{u.id}: {u.name} ({u.email})</li>")
    html.append("</ul></body></html>")
    return "\n".join(html)
