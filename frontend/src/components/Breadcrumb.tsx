interface BreadcrumbProps {
  path: string;
  onNavigate: (path: string) => void;
}

export function Breadcrumb({ path, onNavigate }: BreadcrumbProps) {
  const segments = path.split("/").filter(Boolean); // ["var", "log", "nginx"]

  // Build cumulative path up to and including segment i.
  const segmentPath = (i: number) => "/" + segments.slice(0, i + 1).join("/");

  // Collapse middle segments when more than 5: show first 2 + ellipsis + last 2.
  const COLLAPSE_THRESHOLD = 5;
  let visible: { name: string; path: string; clickable: boolean }[];
  if (segments.length > COLLAPSE_THRESHOLD) {
    const first2 = segments.slice(0, 2).map((name, i) => ({ name, path: segmentPath(i), clickable: true }));
    const last2 = segments.slice(-2).map((name, idx) => {
      const i = segments.length - 2 + idx;
      return { name, path: segmentPath(i), clickable: true };
    });
    visible = [...first2, { name: "…", path: "", clickable: false }, ...last2];
  } else {
    visible = segments.map((name, i) => ({ name, path: segmentPath(i), clickable: true }));
  }

  return (
    <nav aria-label="breadcrumb" style={{ display: "flex", gap: "4px", alignItems: "center" }}>
      <span
        onClick={() => onNavigate("/")}
        style={{ cursor: "pointer" }}
        role="link"
        tabIndex={0}
      >
        /
      </span>
      {visible.map((seg, idx) => (
        <span key={idx} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <span aria-hidden="true">›</span>
          <span
            style={{ cursor: seg.clickable ? "pointer" : "default", color: seg.clickable ? "#06c" : "#999" }}
            onClick={() => seg.clickable && onNavigate(seg.path)}
            role={seg.clickable ? "link" : undefined}
          >
            {seg.name}
          </span>
        </span>
      ))}
    </nav>
  );
}
