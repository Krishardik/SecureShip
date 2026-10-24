"""Regression tests for invalid bearer tokens on protected project routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/projects/1", None),
        ("PATCH", "/projects/1", {"name": "Unauthorized Change"}),
        ("DELETE", "/projects/1", None),
    ],
)
@pytest.mark.parametrize(
    "token",
    [
        "not-a-valid-token",
        "",
        "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0.",
    ],
)
def test_project_endpoints_reject_invalid_bearer_tokens(
    client: TestClient,
    method: str,
    path: str,
    payload: dict | None,
    token: str,
):
    response = client.request(
        method,
        path,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
