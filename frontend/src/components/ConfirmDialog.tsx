import { useState, useEffect } from "react";

interface ConfirmDialogProps {
  open: boolean;
  summary: string;
  writeToken: string;
  onConfirm: (confirmToken: string) => void;
  onCancel: () => void;
}

const CACHE_KEY = "diskviz_write_token_confirmed";

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function ConfirmDialog({
  open,
  summary,
  writeToken,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const [cached, setCached] = useState(false);
  const [typed, setTyped] = useState("");
  const [checked, setChecked] = useState(false);

  // Reset transient state whenever the dialog (re)opens.
  useEffect(() => {
    if (open) {
      setCached(sessionStorage.getItem(CACHE_KEY) === "1");
      setTyped("");
      setChecked(false);
    }
  }, [open]);

  if (!open) return null;

  const canConfirm = cached ? checked : typed === writeToken && typed.length > 0;

  const handleConfirm = async () => {
    if (!canConfirm) return;
    const confirmToken = await sha256Hex(writeToken);
    if (!cached) {
      sessionStorage.setItem(CACHE_KEY, "1");
    }
    onConfirm(confirmToken);
  };

  return (
    <div
      role="dialog"
      aria-label="confirm-dialog"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "6px",
          padding: "16px",
          minWidth: "320px",
          maxWidth: "480px",
          fontFamily: "sans-serif",
        }}
      >
        <h3 style={{ margin: "0 0 8px" }}>操作确认</h3>
        <div style={{ marginBottom: "12px", wordBreak: "break-all" }}>{summary}</div>
        {cached ? (
          <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}>
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
            />
            确认执行此操作
          </label>
        ) : (
          <div style={{ marginBottom: "12px" }}>
            <label
              htmlFor="confirm-write-token"
              style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}
            >
              请输入 write-token 以确认
            </label>
            <input
              id="confirm-write-token"
              aria-label="write-token"
              type="password"
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoComplete="off"
              style={{
                width: "100%",
                padding: "6px 8px",
                border: "1px solid #ccc",
                borderRadius: "3px",
                boxSizing: "border-box",
              }}
            />
          </div>
        )}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <button
            onClick={onCancel}
            style={{
              padding: "6px 14px",
              border: "1px solid #ccc",
              background: "#f2f2f2",
              borderRadius: "3px",
              cursor: "pointer",
            }}
          >
            取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canConfirm}
            style={{
              padding: "6px 14px",
              border: "1px solid #ccc",
              background: canConfirm ? "#e15759" : "#ddd",
              color: canConfirm ? "#fff" : "#999",
              borderRadius: "3px",
              cursor: canConfirm ? "pointer" : "not-allowed",
            }}
          >
            确认
          </button>
        </div>
      </div>
    </div>
  );
}
