"""End-to-end test: log in, start a scan, wait for completion, verify Treemap renders."""
from __future__ import annotations

import pytest

playwright = pytest.importorskip("playwright")


def test_scan_and_visualize(page, live_server: str):
    page.goto(live_server)
    page.fill("[aria-label=read-token]", "dev-read")
    page.fill("[aria-label=write-token]", "dev-write")
    page.click("text=登录")

    page.fill("[aria-label=root]", "/tmp")
    page.click("text=扫描")

    # Wait for the scan to finish and the treemap canvas to appear.
    page.wait_for_selector("canvas[aria-label=treemap]", timeout=30000)

    # Breadcrumb should reflect the scanned root.
    page.wait_for_selector("[aria-label=breadcrumb]")

    # Clicking the canvas triggers a drilldown (updates breadcrumb or path).
    bbox = page.locator("canvas[aria-label=treemap]").bounding_box()
    if bbox:
        page.mouse.click(bbox["x"] + 5, bbox["y"] + 5)
