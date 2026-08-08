import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TokenLogin } from "./TokenLogin";

describe("TokenLogin", () => {
  it("submits with both tokens and calls onLogin", () => {
    const onLogin = vi.fn();
    render(<TokenLogin onLogin={onLogin} />);
    fireEvent.change(screen.getByLabelText(/read-token/i), { target: { value: "r" } });
    fireEvent.change(screen.getByLabelText(/write-token/i), { target: { value: "w" } });
    fireEvent.click(screen.getByRole("button", { name: /login|登录/i }));
    expect(onLogin).toHaveBeenCalledWith("r", "w");
  });

  it("rejects blank submission", () => {
    const onLogin = vi.fn();
    render(<TokenLogin onLogin={onLogin} />);
    fireEvent.click(screen.getByRole("button", { name: /login|登录/i }));
    expect(onLogin).not.toHaveBeenCalled();
  });
});
