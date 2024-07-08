import pytest
from app.main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_authenticate(client):
    rv = client.get("/authenticate", headers={"x-api-key": "test_key"})
    assert rv.status_code == 200

def test_process_request(client):
    rv = client.post("/process_request", json={"webhook_url": "http://example.com"}, headers={"x-api-key": "test_key"})
    assert rv.status_code == 202
