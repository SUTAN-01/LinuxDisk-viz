import { useEffect, useRef, useState, useMemo } from "react";
import { squarify, type LaidOutRect } from "../lib/squarify";
import type { Entry } from "../store";

interface TreemapViewProps {
  entries: Entry[];
  onDrilldown: (path: string) => void;
  minSize?: number;
}

interface Tooltip {
  path: string;
  size: number;
  x: number;
  y: number;
}

// Stable color palette by extension. Unknown/empty → gray.
const PALETTE = [
  "#4e79a7",
  "#f28e2b",
  "#e15759",
  "#76b7b2",
  "#59a14f",
  "#edc948",
  "#b07aa1",
  "#ff9da7",
  "#9c755f",
  "#bab0ac",
];

const colorByKey = (key: string): string => {
  if (!key) return "#bab0ac";
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
  }
  return PALETTE[hash % PALETTE.length];
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes < 1024 * 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  return `${(bytes / 1024 / 1024 / 1024 / 1024).toFixed(2)} TB`;
}

export function hitTest(rects: LaidOutRect[], x: number, y: number): LaidOutRect | null {
  for (const r of rects) {
    if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) {
      return r;
    }
  }
  return null;
}

export function TreemapView({ entries, onDrilldown, minSize = 0 }: TreemapViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);
  const [rects, setRects] = useState<LaidOutRect[]>([]);

  const items = useMemo(() => {
    const filtered = entries.filter((e) => e.size >= minSize && e.size > 0);
    return filtered.map((e) => ({ name: e.path, size: e.size, ext: e.ext, raw: e }));
  }, [entries, minSize]);

  // Render canvas whenever items change or canvas resizes.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const cssW = canvas.clientWidth || 1;
    const cssH = canvas.clientHeight || 1;
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    if (items.length === 0) {
      setRects([]);
      return;
    }

    const laid = squarify(items, { x: 0, y: 0, w: cssW, h: cssH });
    setRects(laid);

    for (let i = 0; i < laid.length; i++) {
      const r = laid[i];
      const ext = items[i].ext;
      ctx.fillStyle = colorByKey(ext);
      ctx.fillRect(r.x, r.y, r.w, r.h);
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1;
      ctx.strokeRect(r.x + 0.5, r.y + 0.5, Math.max(0, r.w - 1), Math.max(0, r.h - 1));
      // Label when rect is large enough.
      if (r.w > 60 && r.h > 20) {
        ctx.fillStyle = "#fff";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "left";
        const label = items[i].name.split("/").pop() || items[i].name;
        ctx.fillText(label.slice(0, Math.floor(r.w / 7)), r.x + 4, r.y + 14);
      }
    }
  }, [items]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hit = hitTest(rects, x, y);
    if (hit) {
      const raw = items.find((it) => it.name === hit.name);
      setTooltip({
        path: hit.name,
        size: raw?.size ?? 0,
        x: e.clientX - rect.left + 12,
        y: e.clientY - rect.top + 12,
      });
    } else {
      setTooltip(null);
    }
  };

  const handleMouseLeave = () => setTooltip(null);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hit = hitTest(rects, x, y);
    if (hit) onDrilldown(hit.name);
  };

  if (entries.length === 0) {
    return (
      <div aria-label="treemap-empty" style={{ padding: "16px", color: "#999" }}>
        无数据 — 请先执行扫描
      </div>
    );
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <canvas
        ref={canvasRef}
        role="img"
        aria-label="treemap"
        style={{ width: "100%", height: "100%", cursor: "pointer", display: "block" }}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      />
      {tooltip && (
        <div
          role="tooltip"
          style={{
            position: "absolute",
            left: tooltip.x,
            top: tooltip.y,
            background: "rgba(0,0,0,0.85)",
            color: "#fff",
            padding: "4px 8px",
            borderRadius: "4px",
            fontSize: "12px",
            pointerEvents: "none",
            maxWidth: "300px",
            wordBreak: "break-all",
          }}
        >
          <div>{tooltip.path}</div>
          <div>{formatSize(tooltip.size)}</div>
        </div>
      )}
    </div>
  );
}
