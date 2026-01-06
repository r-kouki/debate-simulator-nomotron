import { create } from "zustand";

export type UiState = {
  isStartMenuOpen: boolean;
  setStartMenuOpen: (value: boolean) => void;
  toggleStartMenu: () => void;
};

export const useUiStore = create<UiState>((set) => ({
  isStartMenuOpen: false,
  setStartMenuOpen: (value) => set({ isStartMenuOpen: value }),
  toggleStartMenu: () => set((state) => ({ isStartMenuOpen: !state.isStartMenuOpen }))
}));
