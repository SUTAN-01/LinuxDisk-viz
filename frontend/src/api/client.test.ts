import { describe, it, expect, vi } from "vitest";
import { ApiClient } from "./client";

describe("ApiClient", () => {
  it("injects read token header", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    const client = new ApiClient("http://x", "myread", "mywrite");
    client._fetch = fetchMock;
    await client.get("/health");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://x/health",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer myread" }),
      }),
    );
  });

  it("injects write token for post", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    const client = new ApiClient("http://x", "myread", "mywrite");
    client._fetch = fetchMock;
    await client.post("/ops/delete", { path: "/tmp/a" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://x/ops/delete",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer mywrite" }),
      }),
    );
  });

  it("strips trailing slash from baseUrl", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    const client = new ApiClient("http://x/", "r", "w");
    client._fetch = fetchMock;
    await client.get("/health");
    expect(fetchMock).toHaveBeenCalledWith("http://x/health", expect.anything());
  });

  it("throws ApiError on non-ok response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({ detail: "bad token" }),
    });
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    await expect(client.get("/scan")).rejects.toMatchObject({
      status: 401,
      message: "bad token",
    });
  });

  it("sends json body for post", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    await client.post("/scan", { root: "/tmp" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://x/scan",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ root: "/tmp" }),
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      }),
    );
  });

  it("ws builds url with token query param", () => {
    const wsMock = vi.fn();
    vi.stubGlobal("WebSocket", wsMock);
    const client = new ApiClient("http://x", "myread", "mywrite");
    client.ws("/ws/scan/abc");
    expect(wsMock).toHaveBeenCalledWith("ws://x/ws/scan/abc?token=myread");
    vi.unstubAllGlobals();
  });
});
