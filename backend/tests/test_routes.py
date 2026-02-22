"""Tests for crew_routes (health-check and input validation)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestRootEndpoint:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["app"] == "FalconEye"


class TestCrewStreamValidation:
    def test_rejects_blocked_domain(self):
        resp = client.post(
            "/api/crew/stream", json={"target": "pentagon.mil"}
        )
        assert resp.status_code == 422

    def test_rejects_empty_target(self):
        resp = client.post("/api/crew/stream", json={"target": ""})
        assert resp.status_code == 422
