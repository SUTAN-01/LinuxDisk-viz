import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorBanner } from "./ErrorBanner";

describe("ErrorBanner", () => {
  it("renders nothing when no error", () => {
    const { container } = render(<ErrorBanner message={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders red banner with message when error present", () => {
    render(<ErrorBanner message="WS 连接断开，重试中..." />);
    expect(screen.getByText("WS 连接断开，重试中...")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("calls onRetry when retry button clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="WS 连接断开" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: /重试/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("hides retry button when onRetry not provided", () => {
    render(<ErrorBanner message="发生错误" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
