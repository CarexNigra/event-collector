from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_post():
    response = client.post("/store", headers={"Content-type": "application/json"})
    assert response.status_code == 204


def test_post_wrong_media_type():
    response = client.post("/store", headers={"Content-type": "application/x-www-form-urlencoded"})
    assert response.status_code == 415
