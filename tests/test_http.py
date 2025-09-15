import pytest


def test_http_app_smoke():
    # Skip if FastAPI is not available (HTTP adapter is optional)
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from mcp.http_main import create_app

    app = create_app()
    client = TestClient(app)

    r = client.get("/schemas")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "schemas" in data and isinstance(data["schemas"], list)

