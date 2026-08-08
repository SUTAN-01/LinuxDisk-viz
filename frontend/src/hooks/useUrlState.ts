import { useState, useEffect, useCallback, useRef } from "react";
import type { ViewType } from "../store";

function readParam(name: string, fallback: string): string {
  const params = new URLSearchParams(window.location.search);
  return params.get(name) ?? fallback;
}

function pushState(view: string, path: string) {
  const params = new URLSearchParams();
  if (view && view !== "treemap") params.set("view", view);
  if (path && path !== "/") params.set("path", path);
  const qs = params.toString();
  const url = qs ? `/?${qs}` : "/";
  window.history.pushState({}, "", url);
}

export function useUrlState() {
  const [view, setViewState] = useState<ViewType>(() => {
    const v = readParam("view", "treemap");
    return v === "bars" || v === "tree" || v === "treemap" ? v : "treemap";
  });
  const [path, setPathState] = useState<string>(() => readParam("path", "/"));

  // Keep latest values in a ref so the popstate handler reads current state.
  const latest = useRef({ view, path });
  latest.current = { view, path };

  const setView = useCallback((v: ViewType) => {
    setViewState(v);
    pushState(v, latest.current.path);
  }, []);

  const setPath = useCallback((p: string) => {
    setPathState(p);
    pushState(latest.current.view, p);
  }, []);

  useEffect(() => {
    const onPop = () => {
      const v = readParam("view", "treemap");
      const p = readParam("path", "/");
      setViewState(v === "bars" || v === "tree" || v === "treemap" ? v : "treemap");
      setPathState(p);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return { view, path, setView, setPath };
}
