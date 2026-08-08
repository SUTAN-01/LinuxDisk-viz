import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BarListView } from "./BarListView";
import type { Entry } from "../store";

const entries: Entry[] = [
  { path: "/var/log/big.log", size: 100, type: "file", ext: "log" },
  { path: "/var/log/mid.log", size: 50, type: "file", ext: "log" },
  { path: "/var/log/small.log", size: 10, type: "file", ext: "log" },
  { path: "/var/log/tiny.log", size: 1, type: "file", ext: "log" },
];

describe("BarListView", () => {
  it("sorts entries by size descending", () => {
    render(<BarListView entries={entries} onDrilldown={vi.fn()} />);
    const rows = screen.getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("big.log");
    expect(rows[1]).toHaveTextContent("mid.log");
    expect(rows[2]).toHaveTextContent("small.log");
    expect(rows[3]).toHaveTextContent("tiny.log");
  });

  it("respects limit prop to show only top N", () => {
    render(<BarListView entries={entries} onDrilldown={vi.fn()} limit={2} />);
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent("big.log");
    expect(rows[1]).toHaveTextContent("mid.log");
  });

  it("renders bar width proportional to size", () => {
    render(<BarListView entries={entries} onDrilldown={vi.fn()} limit={2} />);
    const bars = screen.getAllByRole("progressbar");
    expect(bars).toHaveLength(2);
    // Largest item = 100% width
    expect(bars[0]).toHaveAttribute("aria-valuenow", "100");
    // Second item (50/100) = 50%
    expect(bars[1]).toHaveAttribute("aria-valuenow", "50");
  });

  it("calls onDrilldown with path when a row is clicked", () => {
    const onDrilldown = vi.fn();
    render(<BarListView entries={entries} onDrilldown={onDrilldown} limit={2} />);
    fireEvent.click(screen.getByText("big.log"));
    expect(onDrilldown).toHaveBeenCalledWith("/var/log/big.log");
  });

  it("renders empty state when no entries", () => {
    render(<BarListView entries={[]} onDrilldown={vi.fn()} />);
    expect(screen.getByText(/无数据/)).toBeInTheDocument();
  });

  it("formats size in human-readable units", () => {
    const big: Entry[] = [
      { path: "/x/gb.bin", size: 2 * 1024 * 1024 * 1024, type: "file", ext: "bin" },
      { path: "/x/kb.bin", size: 2048, type: "file", ext: "bin" },
    ];
    render(<BarListView entries={big} onDrilldown={vi.fn()} />);
    expect(screen.getByText(/2\.00 GB/)).toBeInTheDocument();
    expect(screen.getByText(/2\.0 KB/)).toBeInTheDocument();
  });
});
