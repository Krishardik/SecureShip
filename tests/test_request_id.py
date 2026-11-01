"""Tests for request correlation ID generation and propagation."""

import logging
from uuid import UUID

from fastapi.testclient import TestClient


def test_response_contains_valid_request_id(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200

    request_id = response.headers.get("x-request-id")
    assert request_id is not None

    parsed_id = UUID(request_id)
    assert parsed_id.version == 4


def test_each_request_receives_a_unique_request_id(client: TestClient):
    first_response = client.get("/")
    second_response = client.get("/")

    first_id = first_response.headers.get("x-request-id")
    second_id = second_response.headers.get("x-request-id")

    assert first_id is not None
    assert second_id is not None
    assert first_id != second_id


def test_client_cannot_spoof_server_generated_request_id(
    client: TestClient,
):
    response = client.get(
        "/",
        headers={"X-Request-ID": "attacker-controlled-id"},
    )

    assert response.status_code == 200

    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    assert request_id != "attacker-controlled-id"

    UUID(request_id)


def test_request_id_is_present_on_rejected_oversized_request(
    client: TestClient,
):
    oversized_body = b"x" * (1_048_576 + 1)

    response = client.request(
        "POST",
        "/projects",
        content=oversized_body,
        headers={"Content-Type": "application/octet-stream"},
    )

    assert response.status_code == 413

    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    UUID(request_id)


def test_request_id_is_in_completion_log(
    client: TestClient,
    caplog,
):
    with caplog.at_level(logging.INFO, logger="secureship.security"):
        response = client.get("/")

    assert response.status_code == 200

    records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http.request.completed"
    ]

    assert records

    record = records[-1]

    assert record.request_id == response.headers["x-request-id"]
    assert record.method == "GET"
    assert record.path == "/"
    assert record.status_code == 200
