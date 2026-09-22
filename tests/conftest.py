import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/taskdb_test"

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    """Create a fresh set of tables for one test, then drop them."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """A TestClient whose requests use the isolated test session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task(client):
    """One task already in the database, returned as its response dict."""
    response = client.post(
        "/tasks",
        json={
            "title": "Sample task",
            "description": "Created by a fixture",
            "status": "todo",
            "priority": "high",
        },
    )
    return response.json()
