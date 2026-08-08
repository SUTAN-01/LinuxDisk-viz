import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useUrlState } from "./useUrlState";

describe("useUrlState", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
  });

  it("reads initial view and path from URL", () => {
    window.history.replaceState({}, "", "/?view=bars&path=/var/log");
    const { result } = renderHook(() => useUrlState());
    expect(result.current.view).toBe("bars");
    expect(result.current.path).toBe("/var/log");
  });

  it("defaults to treemap and / when no params", () => {
    const { result } = renderHook(() => useUrlState());
    expect(result.current.view).toBe("treemap");
    expect(result.current.path).toBe("/");
  });

  it("setView pushes new view to URL", () => {
    const { result } = renderHook(() => useUrlState());
    act(() => result.current.setView("bars"));
    expect(result.current.view).toBe("bars");
    expect(window.location.search).toContain("view=bars");
  });

  it("setPath pushes new path to URL", () => {
    const { result } = renderHook(() => useUrlState());
    act(() => result.current.setPath("/etc"));
    expect(result.current.path).toBe("/etc");
    expect(window.location.search).toContain("path=%2Fetc");
  });

  it("syncs from popstate event (back/forward)", async () => {
    const { result } = renderHook(() => useUrlState());
    act(() => result.current.setView("bars"));
    act(() => result.current.setView("tree"));
    expect(result.current.view).toBe("tree");
    // Go back.
    act(() => window.history.back());
    await waitFor(() => expect(result.current.view).toBe("bars"));
  });
});
