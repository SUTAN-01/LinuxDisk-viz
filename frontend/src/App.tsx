import { useStore } from "./store";
import { useUrlState } from "./hooks/useUrlState";
import { TokenLogin } from "./components/TokenLogin";
import { Breadcrumb } from "./components/Breadcrumb";
import { FileDetails } from "./components/FileDetails";
import { TreemapView } from "./views/TreemapView";
import { BarListView } from "./views/BarListView";
import type { ViewType } from "./store";

export default function App() {
  const {
    readToken,
    writeToken,
    setTokens,
    scanId,
    setScanId,
    selectedEntry,
  } = useStore();
  const { view, path, setView, setPath } = useUrlState();

  if (!readToken || !writeToken) {
    return <TokenLogin onLogin={(r, w) => setTokens(r, w)} />;
  }

  const viewButtons: { v: ViewType; label: string }[] = [
    { v: "treemap", label: "Treemap" },
    { v: "bars", label: "条形排行" },
    { v: "tree", label: "目录树" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header
        role="banner"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "8px",
          borderBottom: "1px solid #ccc",
        }}
      >
        <h1 style={{ margin: 0 }}>diskviz</h1>
        <input aria-label="root" placeholder="扫描路径" style={{ flex: 1 }} />
        <button onClick={() => setScanId("placeholder")}>扫描</button>
        <span>token: {readToken.slice(0, 4)}...</span>
      </header>
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        <nav
          style={{
            width: "200px",
            borderRight: "1px solid #ccc",
            padding: "8px",
          }}
        >
          <div>视图</div>
          {viewButtons.map(({ v, label }) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={view === v ? "active" : ""}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "4px 8px",
                margin: "2px 0",
                background: view === v ? "#4e79a7" : "transparent",
                color: view === v ? "#fff" : "#333",
                border: "1px solid #ccc",
                borderRadius: "3px",
                cursor: "pointer",
              }}
            >
              {label}
            </button>
          ))}
          <hr />
          <div>报告</div>
          <div>历史</div>
        </nav>
        <main style={{ flex: 1, padding: "8px", minWidth: 0, display: "flex", flexDirection: "column" }}>
          <Breadcrumb path={path} onNavigate={setPath} />
          <div style={{ flex: 1, minHeight: 0, marginTop: "8px" }}>
            {view === "treemap" ? (
              <TreemapView entries={[]} onDrilldown={setPath} />
            ) : view === "bars" ? (
              <BarListView entries={[]} onDrilldown={setPath} />
            ) : (
              <div style={{ color: "#999" }}>view: {view}</div>
            )}
          </div>
        </main>
        <aside
          style={{
            width: "240px",
            borderLeft: "1px solid #ccc",
            padding: "8px",
            overflowY: "auto",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: "8px" }}>详情</div>
          <FileDetails entry={selectedEntry} onAction={() => {}} />
        </aside>
      </div>
      <footer
        role="contentinfo"
        style={{
          padding: "4px 8px",
          borderTop: "1px solid #ccc",
          fontSize: "12px",
        }}
      >
        scan: {scanId ?? "无"} | WS: 空闲
      </footer>
    </div>
  );
}
