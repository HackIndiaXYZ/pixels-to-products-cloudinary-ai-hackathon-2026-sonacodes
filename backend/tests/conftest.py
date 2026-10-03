"""In-memory database and a configured-but-mocked Cloudinary account."""

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["CLOUDINARY_CLOUD_NAME"] = "test-cloud"
os.environ["CLOUDINARY_API_KEY"] = "123456789012345"
os.environ["CLOUDINARY_API_SECRET"] = "test-secret-value"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.auth_security import auth_rate_limiter


@pytest.fixture(autouse=True)
def reset_database():
    auth_rate_limiter.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        csrf_response = test_client.get("/api/auth/csrf")
        assert csrf_response.status_code == 200
        registration = test_client.post(
            "/api/auth/register",
            headers={"X-CSRF-Token": csrf_response.json()["csrf_token"]},
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Strong-Test-Password-123!",
                "confirm_password": "Strong-Test-Password-123!",
            },
        )
        assert registration.status_code == 201, registration.text
        test_client.headers["X-CSRF-Token"] = registration.json()["csrf_token"]
        yield test_client
