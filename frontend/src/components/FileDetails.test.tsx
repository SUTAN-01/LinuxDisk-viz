import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FileDetails } from "./FileDetails";
import type { Entry } from "../store";

const entry: Entry = {
  path: "/var/log/nginx/access.log",
  size: 1024 * 1024 * 5, // 5 MB
  type: "file",
  ext: "log",
};

describe("FileDetails", () => {
  it("renders empty state when no entry selected", () => {
    render(<FileDetails entry={null} onAction={vi.fn()} />);
    expect(screen.getByText(/未选中/)).toBeInTheDocument();
  });

  it("displays entry metadata", () => {
    render(<FileDetails entry={entry} onAction={vi.fn()} />);
    expect(screen.getByText("access.log")).toBeInTheDocument();
    expect(screen.getByText(/5\.0 MB/)).toBeInTheDocument();
    expect(screen.getByText("文件")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
  });

  it("renders action buttons", () => {
    render(<FileDetails entry={entry} onAction={vi.fn()} />);
    expect(screen.getByRole("button", { name: /下载/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /打包/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /重命名/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /移动/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /删除/i })).toBeInTheDocument();
  });

  it("calls onAction with action and path when button clicked", () => {
    const onAction = vi.fn();
    render(<FileDetails entry={entry} onAction={onAction} />);
    fireEvent.click(screen.getByRole("button", { name: /删除/i }));
    expect(onAction).toHaveBeenCalledWith("delete", entry.path);
  });

  it("disables actions when readonly flag is set", () => {
    render(<FileDetails entry={entry} onAction={vi.fn()} readonly />);
    expect(screen.getByRole("button", { name: /删除/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /重命名/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /移动/i })).toBeDisabled();
    // Download is a read operation, stays enabled.
    expect(screen.getByRole("button", { name: /下载/i })).toBeEnabled();
  });

  it("shows directory marker for dir type", () => {
    const dir: Entry = { path: "/var/log", size: 100, type: "dir", ext: "" };
    render(<FileDetails entry={dir} onAction={vi.fn()} />);
    expect(screen.getByText(/目录/i)).toBeInTheDocument();
  });
});
