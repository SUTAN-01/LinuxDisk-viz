import { useEffect, useRef, useState } from "react";

// Minimal socket interface so tests can inject a fake without implementing
// the full DOM WebSocket.
interface SocketLike {
  onopen: ((e: Event) => void) | null;
  onmessage: ((e: MessageEvent) => void) | null;
  onclose: ((e: CloseEvent) => void) | null;
  onerror: ((e: Event) => void) | null;
  close: () => void;
}

interface ScanProgressProps {
  scanId: string;
  onComplete: (result: DoneFrame) => void;
  onCancel: () => void;
  /** Factory for the WebSocket. Must include auth token in URL. */
  createSocket: () => SocketLike;
}

interface ProgressFrame {
  type: "progress";
  scanned: number;
  dirs: number;
  bytes_so_far: number;
  elapsed_ms: number;
  eta_ms: number;
}

interface WarnFrame {
  type: "warn";
  path: string;
  code: string;
  msg: string;
}

interface DoneFrame {
  type: "done";
  scan_id: string;
  total_entries: number;
  total_bytes: number;
  elapsed_ms: number;
  cache_hits: number;
  cache_misses: number;
  cancelled: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes < 1024 * 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  return `${(bytes / 1024 / 1024 / 1024 / 1024).toFixed(2)} TB`;
}

function formatMs(ms: number): string {
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  const rs = Math.round(s % 60);
  return `${m}m${rs}s`;
}

function formatNum(n: number): string {
  return n.toLocaleString("en-US");
}

export function ScanProgress({ scanId, onComplete, onCancel, createSocket }: ScanProgressProps) {
  const socketRef = useRef<SocketLike | null>(null);
  const [connected, setConnected] = useState(false);
  const [progress, setProgress] = useState<ProgressFrame | null>(null);
  const [warnings, setWarnings] = useState<WarnFrame[]>([]);
  const [showWarnings, setShowWarnings] = useState(false);

  useEffect(() => {
    const socket = createSocket();
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onmessage = (e: MessageEvent) => {
      let frame: any;
      try {
        frame = JSON.parse(e.data);
      } catch {
        return;
      }
      if (frame.type === "progress") {
        setProgress(frame as ProgressFrame);
      } else if (frame.type === "warn") {
        setWarnings((w) => [...w, frame as WarnFrame]);
      } else if (frame.type === "done") {
        onComplete(frame as DoneFrame);
      }
    };
    socket.onclose = () => setConnected(false);

    return () => {
      try {
        socket.close();
      } catch {
        /* already closed */
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId]);

  const pct =
    progress && progress.elapsed_ms + progress.eta_ms > 0
      ? Math.round((progress.elapsed_ms / (progress.elapsed_ms + progress.eta_ms)) * 100)
      : 0;

  const throughput =
    progress && progress.elapsed_ms > 0
      ? Math.round((progress.scanned / (progress.elapsed_ms / 1000)))
      : 0;

  const handleCancel = () => {
    try {
      socketRef.current?.close();
    } catch {
      /* ignore */
    }
    onCancel();
  };

  return (
    <div style={{ padding: "16px", fontFamily: "sans-serif" }} aria-label="scan-progress">
      <div style={{ fontSize: "48px", fontWeight: 700, lineHeight: 1 }}>
        {connected || progress ? `${pct}%` : "连接中…"}
      </div>
      {progress && (
        <div style={{ marginTop: "8px", color: "#555", fontSize: "14px" }}>
          已扫描 <strong>{formatNum(progress.scanned)}</strong> 项 ·{" "}
          {formatBytes(progress.bytes_so_far)} ·{" "}
          {throughput} 项/秒 · ETA {formatMs(progress.eta_ms)}
        </div>
      )}
      <div
        style={{
          height: "8px",
          background: "#eee",
          borderRadius: "4px",
          marginTop: "12px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: "#4e79a7",
            transition: "width 0.3s",
          }}
        />
      </div>
      <div style={{ marginTop: "16px", display: "flex", gap: "8px", alignItems: "center" }}>
        <button
          onClick={handleCancel}
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
        {!connected && <span style={{ color: "#999", fontSize: "13px" }}>连接已断开</span>}
      </div>
      <div style={{ marginTop: "16px" }}>
        <button
          onClick={() => setShowWarnings((s) => !s)}
          style={{
            padding: "4px 10px",
            border: "1px solid #ccc",
            background: "#fff",
            borderRadius: "3px",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          警告 ({warnings.length}) {showWarnings ? "▾" : "▸"}
        </button>
        {showWarnings && warnings.length > 0 && (
          <ul style={{ margin: "8px 0 0", paddingLeft: "20px", fontSize: "13px", color: "#555" }}>
            {warnings.map((w, i) => (
              <li key={i}>
                <code>{w.code}</code> {w.path}: {w.msg}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
