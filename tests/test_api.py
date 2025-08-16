import itertools

from sqlalchemy.orm import Session

from app.models import Address, CreditCard, User

_id_counter = itertools.count(1000)


def create_sample_user(db: Session, with_address=False, with_card=False) -> User:
    """Helper: create and persist a user with optional address/card."""
    user = User(
        external_id=next(_id_counter),
        name="Test User",
        username="testuser",
        email="test@example.com",
        phone="123-456",
        website="example.com",
        company_name="Test Inc",
    )
    db.add(user)
    db.flush()
    if with_address:
        addr = Address(
            user_id=user.id,
            street="123 Main St",
            street_name="Main",
            city="TestCity",
            state="TS",
            country="TC",
            zip="12345",
            lat="0.0",
            lng="0.0",
            raw_json={},
        )
        db.add(addr)

    if with_card:
        cc = CreditCard(
            user_id=user.id,
            cc_number="4111111111111111",
            cc_type="visa",
            exp_month="12",
            exp_year="2030",
            raw_json={},
        )
        db.add(cc)

    db.commit()
    return user


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_users_list(client):
    """Ensure /users returns a list (may be empty or prepopulated)."""
    res = client.get("/users")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_users_list_with_filters(client, db_session):
    u1 = create_sample_user(db_session, with_address=True)
    u2 = create_sample_user(db_session, with_card=True)
    u3 = create_sample_user(db_session)

    res = client.get("/users")
    assert res.status_code == 200
    ids = {u["id"] for u in res.json()}
    assert {u1.id, u2.id, u3.id}.issubset(ids)

    res = client.get("/users", params={"has_address": True})
    ids = {u["id"] for u in res.json()}
    assert u1.id in ids

    res = client.get("/users", params={"has_card": True})
    ids = {u["id"] for u in res.json()}
    assert u2.id in ids


def test_get_user_success(client, db_session):
    user = create_sample_user(db_session, with_card=True)
    res = client.get(f"/users/{user.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == user.id
    assert data["credit_card"]["cc_number"].startswith("****")


def test_get_user_not_found(client):
    res = client.get("/users/99999")
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_ui_users_page(client, db_session):
    create_sample_user(db_session)
    res = client.get("/users/ui")
    assert res.status_code == 200
    text = res.text.lower()
    assert "<html" in text
    assert "<ul" in text
    assert "<li" in text
