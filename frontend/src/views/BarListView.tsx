import { useMemo, useRef, useState, useEffect } from "react";
import type { Entry } from "../store";

interface BarListViewProps {
  entries: Entry[];
  onDrilldown: (path: string) => void;
  limit?: number;
  rowHeight?: number;
  viewportHeight?: number;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes < 1024 * 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  return `${(bytes / 1024 / 1024 / 1024 / 1024).toFixed(2)} TB`;
}

const DEFAULT_ROW_HEIGHT = 28;
const DEFAULT_VIEWPORT_HEIGHT = 600;
const OVERSCAN = 5;

export function BarListView({
  entries,
  onDrilldown,
  limit,
  rowHeight = DEFAULT_ROW_HEIGHT,
  viewportHeight = DEFAULT_VIEWPORT_HEIGHT,
}: BarListViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const sorted = useMemo(() => {
    const arr = [...entries].sort((a, b) => b.size - a.size);
    return limit ? arr.slice(0, limit) : arr;
  }, [entries, limit]);

  useEffect(() => {
    setScrollTop(0);
  }, [sorted.length]);

  if (entries.length === 0) {
    return (
      <div aria-label="bars-empty" style={{ padding: "16px", color: "#999" }}>
        无数据 — 请先执行扫描
      </div>
    );
  }

  const maxSize = sorted.length > 0 ? sorted[0].size : 1;
  const totalHeight = sorted.length * rowHeight;

  // Virtual window: only render rows in the visible range + overscan.
  const startIdx = Math.max(0, Math.floor(scrollTop / rowHeight) - OVERSCAN);
  const visibleCount = Math.ceil(viewportHeight / rowHeight) + OVERSCAN * 2;
  const endIdx = Math.min(sorted.length, startIdx + visibleCount);

  const visible = sorted.slice(startIdx, endIdx);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      role="list"
      aria-label="bar-list"
      style={{
        height: viewportHeight,
        overflowY: "auto",
        position: "relative",
        fontFamily: "sans-serif",
      }}
    >
      <div style={{ height: totalHeight, position: "relative" }}>
        {visible.map((entry, i) => {
          const idx = startIdx + i;
          const pct = maxSize > 0 ? (entry.size / maxSize) * 100 : 0;
          const name = entry.path.split("/").pop() || entry.path;
          return (
            <li
              key={entry.path}
              role="listitem"
              onClick={() => onDrilldown(entry.path)}
              style={{
                position: "absolute",
                top: idx * rowHeight,
                left: 0,
                right: 0,
                height: rowHeight,
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "0 8px",
                cursor: "pointer",
                listStyle: "none",
                boxSizing: "border-box",
                whiteSpace: "nowrap",
              }}
              title={entry.path}
            >
              <span
                style={{
                  width: "180px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  fontSize: "13px",
                }}
              >
                {name}
              </span>
              <div
                role="progressbar"
                aria-valuenow={Math.round(pct)}
                aria-valuemin={0}
                aria-valuemax={100}
                style={{
                  flex: 1,
                  height: "12px",
                  background: "#eee",
                  borderRadius: "3px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    background: "#4e79a7",
                  }}
                />
              </div>
              <span style={{ width: "80px", textAlign: "right", fontSize: "12px", color: "#555" }}>
                {formatSize(entry.size)}
              </span>
            </li>
          );
        })}
      </div>
    </div>
  );
}
