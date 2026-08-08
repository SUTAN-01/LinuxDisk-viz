import { useStore } from "./store";
import { TokenLogin } from "./components/TokenLogin";
import { Breadcrumb } from "./components/Breadcrumb";
import { TreemapView } from "./views/TreemapView";

export default function App() {
  const {
    readToken,
    writeToken,
    setTokens,
    scanId,
    currentPath,
    view,
    setView,
    setScanId,
    setCurrentPath,
  } = useStore();

  if (!readToken || !writeToken) {
    return <TokenLogin onLogin={(r, w) => setTokens(r, w)} />;
  }

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
          <button onClick={() => setView("treemap")}>Treemap</button>
          <button onClick={() => setView("bars")}>条形排行</button>
          <button onClick={() => setView("tree")}>目录树</button>
          <hr />
          <div>报告</div>
          <div>历史</div>
        </nav>
        <main style={{ flex: 1, padding: "8px", minWidth: 0, display: "flex", flexDirection: "column" }}>
          <Breadcrumb path={currentPath} onNavigate={setCurrentPath} />
          <div style={{ flex: 1, minHeight: 0, marginTop: "8px" }}>
            {view === "treemap" ? (
              <TreemapView entries={[]} onDrilldown={setCurrentPath} />
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
          }}
        >
          <div>详情</div>
          <div>操作</div>
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
