import re

import pytest
import responses

from app.models import Address, CreditCard, User
from app.tasks.addresses import enrich_missing_addresses
from app.tasks.credit_cards import enrich_missing_cards
from app.tasks.users import sync_users


@pytest.mark.usefixtures("mock_responses")
def test_sync_users_task(db_session, mock_responses):
    """sync_users should fetch and store users from DummyJSON API."""
    mock_responses.add(
        responses.GET,
        re.compile(r"https://dummyjson\.com/users(\?.*)?$"),
        json={
            "users": [
                {
                    "id": 123,
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "username": "jane",
                    "email": "jane@example.com",
                    "phone": "123456",
                    "website": "example.com",
                    "company": {"name": "Example Inc"},
                }
            ],
            "total": 1,
        },
        status=200,
    )

    sync_users()

    saved = db_session.query(User).filter_by(external_id=123).first()
    assert saved is not None
    assert saved.username == "jane" or (saved.name and saved.name.startswith("Jane"))


@pytest.mark.usefixtures("mock_responses")
def test_enrich_missing_addresses_task(db_session, mock_responses):
    """enrich_missing_addresses should attach address from DummyJSON user details."""
    db_session.query(User).delete()
    db_session.commit()

    user = User(external_id=50, name="Addr Test")
    db_session.add(user)
    db_session.commit()

    mock_responses.add(
        responses.GET,
        re.compile(r"https://dummyjson\.com/users/50$"),
        json={
            "id": 50,
            "firstName": "A",
            "lastName": "B",
            "address": {
                "address": "5 Test St",
                "city": "Testville",
                "state": "TS",
                "stateCode": "TS",
                "postalCode": "99999",
                "coordinates": {"lat": 1.23, "lng": 4.56},
                "country": "Nowhere",
            },
        },
        status=200,
    )

    enrich_missing_addresses()

    saved = db_session.query(Address).filter_by(user_id=user.id).first()
    assert saved is not None
    assert saved.city == "Testville"
    assert saved.country == "Nowhere"
    assert saved.lat == 1.23 and saved.lng == 4.56


@pytest.mark.usefixtures("mock_responses")
def test_enrich_missing_cards_task(db_session, mock_responses):
    """enrich_missing_cards should attach credit card from DummyJSON user 'bank'."""
    db_session.query(User).delete()
    db_session.commit()

    user = User(external_id=51, name="Card Test")
    db_session.add(user)
    db_session.commit()

    mock_responses.add(
        responses.GET,
        re.compile(r"https://dummyjson\.com/users/51$"),
        json={
            "id": 51,
            "firstName": "C",
            "lastName": "D",
            "bank": {
                "cardType": "MasterCard",
                "cardNumber": "1111-2222-3333-4444",
                "cardExpire": "11/2028",
            },
        },
        status=200,
    )

    enrich_missing_cards()

    saved = db_session.query(CreditCard).filter_by(user_id=user.id).first()
    assert saved is not None
    assert saved.cc_type == "MasterCard"
    assert saved.cc_number.endswith("4444")
    assert 1 <= saved.exp_month <= 12
    assert saved.exp_year >= 2025
