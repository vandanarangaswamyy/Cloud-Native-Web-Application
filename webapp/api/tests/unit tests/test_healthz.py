import pytest

@pytest.mark.django_db
def test_healthz_success(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-cache, no-store, must-revalidate"

@pytest.mark.django_db
def test_healthz_with_body(client):
    response = client.get("/healthz", data={"extra": "value"})
    assert response.status_code == 400

@pytest.mark.django_db
def test_healthz_with_query_params(client):
    response = client.get("/healthz?foo=bar")
    assert response.status_code == 400

@pytest.mark.django_db
def test_healthz_endpoint_returns_200(client):
    response = client.get("/healthz")
    assert response.status_code == 200
