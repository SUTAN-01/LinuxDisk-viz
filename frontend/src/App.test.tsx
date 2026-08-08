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
});
