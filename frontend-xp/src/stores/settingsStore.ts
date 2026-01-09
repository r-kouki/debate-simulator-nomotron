import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Settings, defaultSettings } from '@/types/settings';

interface SettingsStore {
  settings: Settings;
  
  // Actions
  updateSettings: (partial: Partial<Settings>) => void;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      settings: defaultSettings,

      updateSettings: (partial) =>
        set((state) => ({
          settings: { ...state.settings, ...partial },
        })),

      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: 'debate-xp-settings',
    }
  )
);
