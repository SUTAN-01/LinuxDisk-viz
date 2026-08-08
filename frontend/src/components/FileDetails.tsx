import type { Entry } from "../store";

export type FileAction = "download" | "pack" | "rename" | "move" | "delete";

interface FileDetailsProps {
  entry: Entry | null;
  onAction: (action: FileAction, path: string) => void;
  readonly?: boolean;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes < 1024 * 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  return `${(bytes / 1024 / 1024 / 1024 / 1024).toFixed(2)} TB`;
}

const WRITE_ACTIONS: FileAction[] = ["pack", "rename", "move", "delete"];

export function FileDetails({ entry, onAction, readonly = false }: FileDetailsProps) {
  if (!entry) {
    return (
      <div aria-label="details-empty" style={{ color: "#999", padding: "8px" }}>
        未选中任何条目
      </div>
    );
  }

  const name = entry.path.split("/").pop() || entry.path;
  const typeLabel = entry.type === "dir" ? "目录" : "文件";
  const actions: { action: FileAction; label: string }[] = [
    { action: "download", label: "下载" },
    { action: "pack", label: "打包" },
    { action: "rename", label: "重命名" },
    { action: "move", label: "移动" },
    { action: "delete", label: "删除" },
  ];

  return (
    <div aria-label="file-details" style={{ padding: "8px", fontFamily: "sans-serif" }}>
      <div style={{ fontWeight: 600, marginBottom: "8px", wordBreak: "break-all" }}>{name}</div>
      <dl style={{ margin: 0, fontSize: "13px", lineHeight: 1.6 }}>
        <div>
          <dt style={{ display: "inline", color: "#888" }}>路径: </dt>
          <dd style={{ display: "inline", wordBreak: "break-all" }}>{entry.path}</dd>
        </div>
        <div>
          <dt style={{ display: "inline", color: "#888" }}>大小: </dt>
          <dd style={{ display: "inline" }}>{formatSize(entry.size)}</dd>
        </div>
        <div>
          <dt style={{ display: "inline", color: "#888" }}>类型: </dt>
          <dd style={{ display: "inline" }}>{typeLabel}</dd>
        </div>
        {entry.ext && (
          <div>
            <dt style={{ display: "inline", color: "#888" }}>扩展名: </dt>
            <dd style={{ display: "inline" }}>{entry.ext}</dd>
          </div>
        )}
      </dl>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "12px" }}>
        {actions.map(({ action, label }) => {
          const isWrite = WRITE_ACTIONS.includes(action);
          const disabled = readonly && isWrite;
          return (
            <button
              key={action}
              onClick={() => !disabled && onAction(action, entry.path)}
              disabled={disabled}
              style={{
                padding: "4px 10px",
                fontSize: "13px",
                cursor: disabled ? "not-allowed" : "pointer",
                background: action === "delete" ? "#e15759" : "#f2f2f2",
                color: action === "delete" ? "#fff" : "#333",
                border: "1px solid #ccc",
                borderRadius: "3px",
                opacity: disabled ? 0.5 : 1,
              }}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
