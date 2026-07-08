"""
Pytest configuration and shared fixtures for the Tiny Bank application.
Defines the test client and handles automatic database resetting for isolation.
"""

import sys
import os
# Force Python to find the root 'app' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
from app.main import app
from app.database import reset_db

@pytest.fixture(autouse=True)
def clean_database():
    """
    Fixture executed automatically before and after each test.
    Resets the in-memory database storage to ensure perfect test isolation.
    """
    reset_db()
    yield
    reset_db()

@pytest.fixture
def client():
    """
    Provides a FastAPI TestClient instance to simulate synchronous HTTP requests in tests.
    """
    with TestClient(app) as test_client:
        yield test_client