from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import app
from producer import create_kafka_producer


@pytest.fixture(scope='session')
def kafka_producer_mock():
    mock = MagicMock()
    mock.produce = MagicMock()
    yield mock


@pytest.fixture(scope="function", autouse=True)
def reset_mock(kafka_producer_mock):
    # NB: This function is neaded to reset kafka producer
    # Otherwise within session the fact that kafka_producer_mock was 
    # called for the first test, would give asser error in subsequent tests
    # This function is called automatically after each call of the kafka_producer_mock
    # Which is called once per test function. 
    yield
    kafka_producer_mock.reset_mock()


@pytest.fixture(scope='session')
def client(kafka_producer_mock):
    app.dependency_overrides[create_kafka_producer] = lambda: kafka_producer_mock 
    # NB: lambda is needed to return function. without it it will return object
    yield TestClient(app)