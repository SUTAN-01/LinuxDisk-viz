import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Breadcrumb } from "./Breadcrumb";

describe("Breadcrumb", () => {
  it("renders path segments", () => {
    render(<Breadcrumb path="/var/log/nginx" onNavigate={vi.fn()} />);
    expect(screen.getByText("var")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("nginx")).toBeInTheDocument();
  });

  it("calls onNavigate with segment path when clicked", () => {
    const onNavigate = vi.fn();
    render(<Breadcrumb path="/var/log/nginx" onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("log"));
    expect(onNavigate).toHaveBeenCalledWith("/var/log");
  });

  it("collapses middle segments with ellipsis when more than 5", () => {
    render(<Breadcrumb path="/a/b/c/d/e/f" onNavigate={vi.fn()} />);
    expect(screen.getByText("a")).toBeInTheDocument();
    expect(screen.getByText("b")).toBeInTheDocument();
    expect(screen.getByText("f")).toBeInTheDocument();
    expect(screen.getByText(/…|(\.\.\.)/)).toBeInTheDocument(); // ellipsis
    expect(screen.queryByText("c")).not.toBeInTheDocument(); // middle hidden
    expect(screen.queryByText("d")).not.toBeInTheDocument(); // middle hidden
  });

  it("navigates to root when root clicked", () => {
    const onNavigate = vi.fn();
    render(<Breadcrumb path="/var/log" onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("/")); // root element
    expect(onNavigate).toHaveBeenCalledWith("/");
  });

  it("clicking last segment navigates to full path", () => {
    const onNavigate = vi.fn();
    render(<Breadcrumb path="/var/log/nginx" onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("nginx"));
    expect(onNavigate).toHaveBeenCalledWith("/var/log/nginx");
  });
});
