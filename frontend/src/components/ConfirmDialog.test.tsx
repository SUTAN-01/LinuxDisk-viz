import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ConfirmDialog } from "./ConfirmDialog";

describe("ConfirmDialog", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("shows the operation summary when open", () => {
    render(
      <ConfirmDialog
        open
        summary="删除 1 个文件"
        writeToken="wt"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText("删除 1 个文件")).toBeInTheDocument();
  });

  it("renders nothing when not open", () => {
    render(
      <ConfirmDialog
        open={false}
        summary="删除 1 个文件"
        writeToken="wt"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.queryByText("删除 1 个文件")).not.toBeInTheDocument();
  });

  it("disables confirm button until write-token is entered correctly", () => {
    render(
      <ConfirmDialog
        open
        summary="删除 1 个文件"
        writeToken="wt"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    const confirmBtn = screen.getByRole("button", { name: /确认/ });
    expect(confirmBtn).toBeDisabled();

    // Wrong token does not enable.
    fireEvent.change(screen.getByLabelText(/write-token/i), {
      target: { value: "wrong" },
    });
    expect(confirmBtn).toBeDisabled();

    // Correct token enables.
    fireEvent.change(screen.getByLabelText(/write-token/i), {
      target: { value: "wt" },
    });
    expect(confirmBtn).toBeEnabled();
  });

  it("calls onConfirm with sha256 hex of write-token on confirm", async () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        summary="删除 1 个文件"
        writeToken="wt"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText(/write-token/i), {
      target: { value: "wt" },
    });
    fireEvent.click(screen.getByRole("button", { name: /确认/ }));
    await waitFor(() => expect(onConfirm).toHaveBeenCalledTimes(1));
    const arg = onConfirm.mock.calls[0][0];
    // sha256 hex string
    expect(arg).toMatch(/^[0-9a-f]{64}$/);
  });

  it("cancel does not trigger onConfirm", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        summary="删除 1 个文件"
        writeToken="wt"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /取消/ }));
    expect(onConfirm).not.toHaveBeenCalled();
    expect(onCancel).toHaveBeenCalled();
  });

  it("uses cached confirmation after first success (checkbox mode)", async () => {
    const onConfirm = vi.fn();
    const { unmount } = render(
      <ConfirmDialog
        open
        summary="删除 1 个文件"
        writeToken="wt"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText(/write-token/i), {
      target: { value: "wt" },
    });
    fireEvent.click(screen.getByRole("button", { name: /确认/ }));
    await waitFor(() => expect(onConfirm).toHaveBeenCalledTimes(1));
    unmount();

    // Second render: should show checkbox, button enabled without retyping.
    const onConfirm2 = vi.fn();
    render(
      <ConfirmDialog
        open
        summary="移动 2 个文件"
        writeToken="wt"
        onConfirm={onConfirm2}
        onCancel={vi.fn()}
      />,
    );
    // No write-token input this time.
    expect(screen.queryByLabelText(/write-token/i)).not.toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox", { name: /记住|确认/i });
    const confirmBtn = screen.getByRole("button", { name: /确认/ });
    expect(confirmBtn).toBeDisabled();
    fireEvent.click(checkbox);
    expect(confirmBtn).toBeEnabled();
    fireEvent.click(confirmBtn);
    await waitFor(() => expect(onConfirm2).toHaveBeenCalledTimes(1));
  });
});
