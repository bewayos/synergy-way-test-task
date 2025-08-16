import os

import pytest
import responses as responses_lib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")

engine = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provide a fresh database session for each test function."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def patch_sessionlocal(monkeypatch, db_session):
    """
    Ensure app.db.SessionLocal used by session_scope() creates sessions bound
    to our test engine/session, so tasks write to the same DB the tests read from.
    """
    import app.db as app_db

    monkeypatch.setattr(app_db, "SessionLocal", TestingSessionLocal, raising=False)
    yield


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client (якщо знадобиться для API-тестів)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_responses():
    """Provide a responses mocker for external HTTP calls."""
    with responses_lib.RequestsMock() as rsps:
        yield rsps
