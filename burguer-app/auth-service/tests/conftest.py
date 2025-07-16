# conftest.py Establishes fixtures for testing with pytest
# This file sets up a MongoDB client and a test database for the auth service tests.

import pytest
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def mongo_client():
    # Connects to the MongoDB using the URI from environment variables
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    yield client
    client.close()

@pytest.fixture(scope="function")
# Provides a test database instance for each test function
def test_db(mongo_client):
    db = mongo_client["burguer_app_db"]
    db["users"].delete_many({})
    db["pedido"].delete_many({})

    yield db