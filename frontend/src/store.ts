import { create } from "zustand";

export type ViewType = "treemap" | "bars" | "tree";

export interface Entry {
  path: string;
  size: number;
  type: string;
  ext: string;
}

interface AppState {
  readToken: string;
  writeToken: string;
  setTokens: (read: string, write: string) => void;
  scanId: string | null;
  setScanId: (id: string | null) => void;
  currentPath: string;
  setCurrentPath: (p: string) => void;
  view: ViewType;
  setView: (v: ViewType) => void;
  selectedEntry: Entry | null;
  setSelectedEntry: (e: Entry | null) => void;
}

export const useStore = create<AppState>((set) => ({
  readToken: "",
  writeToken: "",
  setTokens: (read, write) => set({ readToken: read, writeToken: write }),
  scanId: null,
  setScanId: (id) => set({ scanId: id }),
  currentPath: "/",
  setCurrentPath: (p) => set({ currentPath: p }),
  view: "treemap",
  setView: (v) => set({ view: v }),
  selectedEntry: null,
  setSelectedEntry: (e) => set({ selectedEntry: e }),
}));
