from app.models import Address, CreditCard, User


def test_user_mapping(db_session):
    """Check mapping from JSONPlaceholder user data to User model."""
    user_data = {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
        "phone": "1-770-736-8031",
        "website": "hildegard.org",
        "company": {"name": "Romaguera-Crona"},
    }
    user = User(
        external_id=user_data["id"],
        name=user_data["name"],
        username=user_data["username"],
        email=user_data["email"],
        phone=user_data["phone"],
        website=user_data["website"],
        company_name=user_data["company"]["name"],
    )
    db_session.add(user)
    db_session.commit()

    saved = db_session.query(User).filter_by(external_id=1).first()
    assert saved is not None
    assert saved.name == "Leanne Graham"
    assert saved.company_name == "Romaguera-Crona"


def test_address_mapping(db_session):
    """Check mapping from Random-Data API address JSON to Address model."""
    address_data = {
        "street_address": "123 Main St",
        "street_name": "Main",
        "city": "Metropolis",
        "state": "NY",
        "country": "USA",
        "zip_code": "12345",
        "latitude": 40.7128,
        "longitude": -74.0060,
    }
    address = Address(
        user_id=1,
        street=address_data["street_address"],
        street_name=address_data["street_name"],
        city=address_data["city"],
        state=address_data["state"],
        country=address_data["country"],
        zip=address_data["zip_code"],
        lat=address_data["latitude"],
        lng=address_data["longitude"],
        raw_json=address_data,
    )
    db_session.add(address)
    db_session.commit()

    saved = db_session.query(Address).filter_by(user_id=1).first()
    assert saved is not None
    assert saved.city == "Metropolis"
    assert "street_address" in saved.raw_json


def test_credit_card_mapping(db_session):
    """Check mapping from Random-Data API credit card JSON to CreditCard model."""
    cc_data = {
        "credit_card_number": "1234-5678-9876-5432",
        "credit_card_type": "Visa",
        "credit_card_expiry_date": "2026-12-01",
    }
    cc = CreditCard(
        user_id=1,
        cc_number=cc_data["credit_card_number"],
        cc_type=cc_data["credit_card_type"],
        exp_month=12,
        exp_year=2026,
        raw_json=cc_data,
    )
    db_session.add(cc)
    db_session.commit()

    saved = db_session.query(CreditCard).filter_by(user_id=1).first()
    assert saved is not None
    assert saved.cc_type == "Visa"
