export interface Settings {
  // Appearance
  wallpaper: string;
  theme: 'bliss' | 'azul' | 'custom';
  customWallpaper?: string;

  // Debate Settings
  defaultRounds: number;
  useInternet: boolean;
  recommendGuests: boolean;
  autoSaveResults: boolean;

  // Window Settings
  windowAnimation: boolean;
  soundEffects: boolean;

  // Advanced
  apiEndpoint: string;
  debugMode: boolean;
}

export const defaultSettings: Settings = {
  wallpaper: 'bliss',
  theme: 'bliss',
  defaultRounds: 2,
  useInternet: false,
  recommendGuests: false,
  autoSaveResults: true,
  windowAnimation: true,
  soundEffects: true,
  apiEndpoint: 'http://localhost:8001/api',
  debugMode: false,
};
