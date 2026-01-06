/**
 * Theme Module - Public API
 */

export { defaultTheme, FONT_ALLOWLIST } from "./defaultTheme";
export { previewTheme, applyAndPersist, resetTheme, getDefaultTheme } from "./applyTheme";
export { saveTheme, loadTheme, clearTheme, hasStoredTheme } from "./storage";

import { loadTheme } from "./storage";
import { previewTheme } from "./applyTheme";

/**
 * Initialize theme on app startup
 * Loads and applies stored theme if present
 */
export const initializeAiTheme = (): void => {
  const stored = loadTheme();
  if (stored) {
    previewTheme(stored);
  }
};
