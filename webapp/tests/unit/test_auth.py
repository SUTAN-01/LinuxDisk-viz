import hashlib
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from diskviz_api.auth import require_token, verify_confirm_token

def _make_app(require_write: bool):
    app = FastAPI()
    @app.get("/x")
    async def x(user=Depends(require_token(require_write))):
        return {"scope": user["scope"]}
    return app

def test_read_token_passes_read_ops():
    client = TestClient(_make_app(require_write=False))
    r = client.get("/x", headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 200
    assert r.json()["scope"] == "read"

def test_read_token_rejects_write_ops():
    client = TestClient(_make_app(require_write=True))
    r = client.get("/x", headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 401

def test_write_token_passes_all():
    client = TestClient(_make_app(require_write=True))
    r = client.get("/x", headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 200
    assert r.json()["scope"] == "write"

def test_no_token_returns_401():
    client = TestClient(_make_app(require_write=False))
    r = client.get("/x")
    assert r.status_code == 401

def test_verify_confirm_token_accepts_write_token_sha256():
    confirm = hashlib.sha256(b"dev-write").hexdigest()
    assert verify_confirm_token(confirm) is True

def test_verify_confirm_token_rejects_wrong():
    assert verify_confirm_token("wrong") is False
    assert verify_confirm_token("") is False
