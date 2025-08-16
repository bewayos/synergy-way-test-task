from app.models import User


def test_user_upsert_idempotent(db_session):
    """Upsert by external_id should not create duplicates; updates existing row."""
    user1 = User(external_id=99, name="Test User", username="test", email="t@t.com")
    db_session.add(user1)
    db_session.commit()

    existing = db_session.query(User).filter_by(external_id=99).one()

    # prepare "updated" user and assign the same PK -> merge will UPDATE, not INSERT
    user2 = User(
        id=existing.id,
        external_id=99,
        name="Test User Updated",
        username="test2",
        email="t2@t.com",
    )
    db_session.merge(user2)
    db_session.commit()

    all_users = db_session.query(User).filter_by(external_id=99).all()
    assert len(all_users) == 1
    assert all_users[0].name == "Test User Updated"
    assert all_users[0].username == "test2"
    assert all_users[0].email == "t2@t.com"
