import { apiClient } from './client';
import { Settings } from '@/types';

export const settingsApi = {
  /**
   * Get current settings
   */
  getSettings: async (): Promise<Settings> => {
    const response = await apiClient.get<any>('/settings');
    return mapApiSettings(response.data);
  },

  /**
   * Update settings
   */
  updateSettings: async (settings: Partial<Settings>): Promise<Settings> => {
    const response = await apiClient.put<any>('/settings', mapSettingsToApi(settings));
    return mapApiSettings(response.data);
  },
};

function mapApiSettings(data: any): Settings {
  return {
    wallpaper: data.wallpaper,
    theme: data.theme,
    defaultRounds: data.default_rounds,
    useInternet: data.use_internet,
    recommendGuests: data.recommend_guests,
    autoSaveResults: data.auto_save_results,
    windowAnimation: data.window_animation,
    soundEffects: data.sound_effects,
    apiEndpoint: data.api_endpoint,
    debugMode: data.debug_mode,
  };
}

function mapSettingsToApi(settings: Partial<Settings>): any {
  return {
    wallpaper: settings.wallpaper,
    theme: settings.theme,
    default_rounds: settings.defaultRounds,
    use_internet: settings.useInternet,
    recommend_guests: settings.recommendGuests,
    auto_save_results: settings.autoSaveResults,
    window_animation: settings.windowAnimation,
    sound_effects: settings.soundEffects,
    api_endpoint: settings.apiEndpoint,
    debug_mode: settings.debugMode,
  };
}
