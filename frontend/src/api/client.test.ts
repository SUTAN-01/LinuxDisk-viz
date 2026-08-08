import { describe, it, expect, vi } from "vitest";
import { ApiClient } from "./client";

describe("ApiClient", () => {
  it("injects read token header", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({}),
    });
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
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({}),
    });
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
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({}),
    });
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
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({}),
    });
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

  it("parses json response body", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: () => Promise.resolve({ scan_id: "abc" }),
    });
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    const result = await client.get("/scan/abc");
    expect(result).toEqual({ scan_id: "abc" });
  });

  it("injects write token for delete", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers(),
      json: () => Promise.resolve({ cancelled: true }),
    });
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    await client.delete("/scan/abc");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://x/scan/abc",
      expect.objectContaining({
        method: "DELETE",
        headers: expect.objectContaining({ Authorization: "Bearer w" }),
      }),
    );
  });

  it("ws converts https to wss", () => {
    const wsMock = vi.fn();
    vi.stubGlobal("WebSocket", wsMock);
    const client = new ApiClient("https://x", "r", "w");
    client.ws("/ws/scan/abc");
    expect(wsMock).toHaveBeenCalledWith("wss://x/ws/scan/abc?token=r");
    vi.unstubAllGlobals();
  });

  it("fires onUnauthorized on 401", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({ detail: "bad token" }),
    });
    const onUnauthorized = vi.fn();
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    client.onUnauthorized = onUnauthorized;
    await expect(client.get("/scan")).rejects.toMatchObject({ status: 401 });
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it("fires onConfirmFailed on 403", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      json: () => Promise.resolve({ detail: "confirm token invalid" }),
    });
    const onConfirmFailed = vi.fn();
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    client.onConfirmFailed = onConfirmFailed;
    await expect(client.post("/ops/delete", { paths: [] })).rejects.toMatchObject({
      status: 403,
    });
    expect(onConfirmFailed).toHaveBeenCalledTimes(1);
  });

  it("does not fire callbacks on ok responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: () => Promise.resolve({}),
    });
    const onUnauthorized = vi.fn();
    const onConfirmFailed = vi.fn();
    const client = new ApiClient("http://x", "r", "w");
    client._fetch = fetchMock;
    client.onUnauthorized = onUnauthorized;
    client.onConfirmFailed = onConfirmFailed;
    await client.get("/health");
    expect(onUnauthorized).not.toHaveBeenCalled();
    expect(onConfirmFailed).not.toHaveBeenCalled();
  });
});
