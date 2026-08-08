import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import App from "./App";
import { useStore } from "./store";

describe("App", () => {
  beforeEach(() => {
    useStore.setState({
      readToken: "",
      writeToken: "",
      scanId: null,
      currentPath: "/",
      view: "treemap",
      selectedEntry: null,
    });
    window.history.replaceState({}, "", "/");
  });

  it("renders diskviz title", () => {
    render(<App />);
    expect(screen.getByText(/diskviz/i)).toBeInTheDocument();
  });

  it("renders three-pane layout with breadcrumb and sidebar", () => {
    useStore.getState().setTokens("r", "w");
    render(<App />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByText(/视图/i)).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("syncs view and path to URL query params", () => {
    window.history.pushState({}, "", "/?view=bars&path=/var/log");
    useStore.getState().setTokens("r", "w");
    render(<App />);
    expect(screen.getByText(/条形排行/)).toHaveClass("active");
  });

  it("marks treemap button active by default", () => {
    useStore.getState().setTokens("r", "w");
    render(<App />);
    expect(screen.getByText("Treemap")).toHaveClass("active");
  });
});
