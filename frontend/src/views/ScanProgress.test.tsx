import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ScanProgress } from "./ScanProgress";

// Minimal fake WebSocket that lets tests push frames.
class FakeSocket {
  onopen: ((e: Event) => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onclose: ((e: CloseEvent) => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  closed = false;

  send(_data: string) {}

  close() {
    this.closed = true;
    this.onclose?.(new CloseEvent("close"));
  }

  emit(frame: object) {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(frame) }),
    );
  }

  open() {
    this.onopen?.(new Event("open"));
  }
}

describe("ScanProgress", () => {
  it("updates progress display when WS sends progress frame", () => {
    const socket = new FakeSocket();
    render(
      <ScanProgress
        scanId="scan-1"
        createSocket={() => socket}
        onComplete={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    act(() => socket.open());
    act(() => {
      socket.emit({
        type: "progress",
        scanned: 12345,
        dirs: 100,
        bytes_so_far: 1024 * 1024 * 100,
        elapsed_ms: 5000,
        eta_ms: 1500,
      });
    });
    expect(screen.getByText(/12,345/)).toBeInTheDocument();
    // pct = elapsed / (elapsed + eta) = 5000/6500 ≈ 77%
    expect(screen.getByText(/77%/)).toBeInTheDocument();
  });

  it("triggers onComplete when done frame arrives", () => {
    const socket = new FakeSocket();
    const onComplete = vi.fn();
    render(
      <ScanProgress
        scanId="scan-1"
        createSocket={() => socket}
        onComplete={onComplete}
        onCancel={vi.fn()}
      />,
    );
    act(() => socket.open());
    act(() => {
      socket.emit({
        type: "done",
        scan_id: "scan-1",
        total_entries: 999,
        total_bytes: 4096,
        elapsed_ms: 3000,
        cache_hits: 10,
        cache_misses: 989,
        cancelled: false,
      });
    });
    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onComplete.mock.calls[0][0].total_entries).toBe(999);
  });

  it("appends warn frames to the warnings list", () => {
    const socket = new FakeSocket();
    render(
      <ScanProgress
        scanId="scan-1"
        createSocket={() => socket}
        onComplete={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    act(() => socket.open());
    act(() => {
      socket.emit({ type: "warn", path: "/root/secret", code: "EACCES", msg: "permission denied" });
    });
    // Warnings are collapsed by default; expand them.
    fireEvent.click(screen.getByRole("button", { name: /警告/ }));
    expect(screen.getByText(/permission denied/)).toBeInTheDocument();
  });

  it("cancel button calls onCancel and closes socket", () => {
    const socket = new FakeSocket();
    const onCancel = vi.fn();
    render(
      <ScanProgress
        scanId="scan-1"
        createSocket={() => socket}
        onComplete={vi.fn()}
        onCancel={onCancel}
      />,
    );
    act(() => socket.open());
    fireEvent.click(screen.getByRole("button", { name: /取消/ }));
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(socket.closed).toBe(true);
  });

  it("shows connecting state before socket opens", () => {
    const socket = new FakeSocket();
    render(
      <ScanProgress
        scanId="scan-1"
        createSocket={() => socket}
        onComplete={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText(/连接中|等待/i)).toBeInTheDocument();
  });
});
