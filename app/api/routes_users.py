from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.db import SessionLocal
from app.models import Address, CreditCard, User
from app.schemas import UserOut
from app.utils.masking import mask_credit_card

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="app/templates")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ui", response_class=HTMLResponse)
def ui_list_users(request: Request, db: Annotated[Session, Depends(get_db)]):
    """
    Minimal HTML page to browse saved users.
    """
    users = db.query(User).all()
    return templates.TemplateResponse(request, "ui.html", {"users": users})


@router.get("", response_model=list[UserOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    has_address: bool | None = Query(None),
    has_card: bool | None = Query(None),
):
    query = db.query(User)

    if has_address is True:
        query = query.join(Address, Address.user_id == User.id)
    elif has_card is False:
        query = query.outerjoin(CreditCard, CreditCard.user_id == User.id).filter(
            CreditCard.id.is_(None)
        )

    if has_card is True:
        query = query.join(CreditCard, CreditCard.user_id == User.id)
    elif has_card is False:
        query = query.outerjoin(CreditCard, CreditCard.user_id == User.id).filter(
            CreditCard.id.is_(None)
        )

    query = query.options(joinedload(User.address), joinedload(User.credit_card))

    users = query.offset(offset).limit(limit).all()

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
