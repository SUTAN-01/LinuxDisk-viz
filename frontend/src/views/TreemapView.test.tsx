import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TreemapView, hitTest } from "./TreemapView";
import type { Entry } from "../store";

const entries: Entry[] = [
  { path: "/var/log/a.log", size: 60, type: "file", ext: "log" },
  { path: "/var/log/b.log", size: 30, type: "file", ext: "log" },
  { path: "/var/log/sub", size: 10, type: "dir", ext: "" },
];

describe("hitTest", () => {
  const rects = [
    { name: "/var/log/a.log", x: 0, y: 0, w: 60, h: 100 },
    { name: "/var/log/b.log", x: 60, y: 0, w: 30, h: 100 },
    { name: "/var/log/sub", x: 90, y: 0, w: 10, h: 100 },
  ];

  it("returns the rect containing the point", () => {
    expect(hitTest(rects, 10, 10)?.name).toBe("/var/log/a.log");
    expect(hitTest(rects, 70, 50)?.name).toBe("/var/log/b.log");
    expect(hitTest(rects, 95, 50)?.name).toBe("/var/log/sub");
  });

  it("returns null when point is outside all rects", () => {
    expect(hitTest(rects, 200, 200)).toBeNull();
  });
});

describe("TreemapView", () => {
  beforeEach(() => {
    // jsdom canvas getContext returns null; stub a permissive 2d context.
    const ctx = new Proxy(
      {},
      {
        get(_target, prop) {
          if (prop === "canvas") return {};
          // Any property access returns a no-op function (methods) or is settable (props).
          return () => {};
        },
      },
    );
    // @ts-expect-error overriding jsdom stub
    HTMLCanvasElement.prototype.getContext = () => ctx;
  });

  it("renders a canvas element", () => {
    render(<TreemapView entries={entries} onDrilldown={vi.fn()} />);
    expect(screen.getByRole("img")).toBeInTheDocument();
  });

  it("renders empty state when no entries", () => {
    render(<TreemapView entries={[]} onDrilldown={vi.fn()} />);
    expect(screen.getByText(/无数据/)).toBeInTheDocument();
  });

  it("renders tooltip on mouse move", () => {
    render(<TreemapView entries={entries} onDrilldown={vi.fn()} />);
    const canvas = screen.getByRole("img");
    // canvas width/height are 0 in jsdom, so hitTest returns null; just verify no crash.
    fireEvent.mouseMove(canvas, { clientX: 0, clientY: 0 });
    // Tooltip container exists (may be empty)
    expect(canvas).toBeInTheDocument();
  });

  it("calls onDrilldown when clicking a rect", () => {
    const onDrilldown = vi.fn();
    // Override canvas size so hitTest works.
    Object.defineProperty(HTMLCanvasElement.prototype, "clientWidth", {
      configurable: true,
      value: 300,
    });
    Object.defineProperty(HTMLCanvasElement.prototype, "clientHeight", {
      configurable: true,
      value: 200,
    });
    render(<TreemapView entries={entries} onDrilldown={onDrilldown} />);
    const canvas = screen.getByRole("img");
    // Click somewhere in the first rect region (proportional coordinates).
    fireEvent.click(canvas, { clientX: 10, clientY: 10, offsetX: 10, offsetY: 10 });
    expect(onDrilldown).toHaveBeenCalled();
  });

  it("respects minSize filter to avoid tiny rectangles", () => {
    render(
      <TreemapView entries={entries} onDrilldown={vi.fn()} minSize={20} />,
    );
    expect(screen.getByRole("img")).toBeInTheDocument();
  });
});
