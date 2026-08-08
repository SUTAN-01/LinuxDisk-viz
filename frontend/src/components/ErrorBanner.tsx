interface ErrorBannerProps {
  message: string | null;
  onRetry?: () => void;
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  if (!message) return null;

  return (
    <div
      role="alert"
      style={{
        background: "#e15759",
        color: "#fff",
        padding: "6px 12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: "13px",
        fontFamily: "sans-serif",
      }}
    >
      <span>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            background: "rgba(255,255,255,0.2)",
            border: "1px solid rgba(255,255,255,0.4)",
            color: "#fff",
            padding: "2px 10px",
            borderRadius: "3px",
            cursor: "pointer",
          }}
        >
          重试
        </button>
      )}
    </div>
  );
}
