import { describe, it, expect } from "vitest";
import { squarify } from "./squarify";

describe("squarify", () => {
  it("partitions rectangle by size proportionally", () => {
    const items = [
      { name: "a", size: 60 },
      { name: "b", size: 30 },
      { name: "c", size: 10 },
    ];
    const rects = squarify(items, { x: 0, y: 0, w: 100, h: 100 });
    expect(rects).toHaveLength(3);
    const totalArea = rects.reduce((s, r) => s + r.w * r.h, 0);
    expect(totalArea).toBeCloseTo(10000, -1);
  });

  it("assigns larger items bigger rectangles", () => {
    const items = [
      { name: "big", size: 90 },
      { name: "small", size: 10 },
    ];
    const rects = squarify(items, { x: 0, y: 0, w: 100, h: 100 });
    const big = rects.find((r) => r.name === "big")!;
    const small = rects.find((r) => r.name === "small")!;
    expect(big.w * big.h).toBeGreaterThan(small.w * small.h);
  });

  it("returns empty array for empty input", () => {
    expect(squarify([], { x: 0, y: 0, w: 100, h: 100 })).toEqual([]);
  });

  it("skips zero-size items", () => {
    const items = [
      { name: "a", size: 50 },
      { name: "zero", size: 0 },
      { name: "b", size: 50 },
    ];
    const rects = squarify(items, { x: 0, y: 0, w: 100, h: 100 });
    expect(rects).toHaveLength(2);
    expect(rects.find((r) => r.name === "zero")).toBeUndefined();
  });

  it("keeps rectangles inside the container bounds", () => {
    const items = [
      { name: "a", size: 40 },
      { name: "b", size: 30 },
      { name: "c", size: 20 },
      { name: "d", size: 10 },
    ];
    const container = { x: 10, y: 20, w: 200, h: 150 };
    const rects = squarify(items, container);
    for (const r of rects) {
      expect(r.x).toBeGreaterThanOrEqual(container.x);
      expect(r.y).toBeGreaterThanOrEqual(container.y);
      expect(r.x + r.w).toBeLessThanOrEqual(container.x + container.w + 1e-6);
      expect(r.y + r.h).toBeLessThanOrEqual(container.y + container.h + 1e-6);
    }
  });
});
