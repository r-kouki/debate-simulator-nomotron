import { create } from "zustand";

export type ApiStatusState = {
  lastError?: string;
  lastChecked?: string;
  online: boolean;
  setStatus: (online: boolean, message?: string) => void;
};

export const useApiStatusStore = create<ApiStatusState>((set) => ({
  online: true,
  lastError: undefined,
  lastChecked: undefined,
  setStatus: (online, message) =>
    set({
      online,
      lastError: message,
      lastChecked: new Date().toISOString()
    })
}));
