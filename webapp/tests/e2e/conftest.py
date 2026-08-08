"""Pytest fixtures for Playwright E2E tests.

Boots a real uvicorn server with dev tokens and provides a Playwright
browser page. Requires: pip install -e ".[e2e]" && playwright install chromium.
"""
from __future__ import annotations

import os
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

os.environ.setdefault("DISKVIZ_READ_TOKEN", "dev-read")
os.environ.setdefault("DISKVIZ_WRITE_TOKEN", "dev-write")
# Point at the mock scanner so the test does not need the C++ binary.
os.environ.setdefault(
    "DISKVIZ_SCANNER_BINARY",
    str(Path(__file__).parent.parent.parent / "tests" / "fixtures" / "mock_scanner.py"),
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server() -> str:
    from diskviz_api.main import app

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    # Wait until the server responds.
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.2)
    yield base
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def page(live_server: str):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        pg._live_server = live_server  # type: ignore[attr-defined]
        yield pg
        context.close()
        browser.close()
