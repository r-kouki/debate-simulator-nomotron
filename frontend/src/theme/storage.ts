/**
 * Theme Persistence - localStorage management
 */

import type { AiTheme } from "../api/types";

const STORAGE_KEY = "debate_sim_theme_v1";

/**
 * Save theme to localStorage
 */
export const saveTheme = (theme: AiTheme): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(theme));
  } catch (e) {
    console.warn("Failed to save theme to localStorage:", e);
  }
};

/**
 * Load theme from localStorage
 * Returns null if no theme stored or parse error
 */
export const loadTheme = (): AiTheme | null => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored) as AiTheme;
  } catch (e) {
    console.warn("Failed to load theme from localStorage:", e);
    return null;
  }
};

/**
 * Clear stored theme
 */
export const clearTheme = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.warn("Failed to clear theme from localStorage:", e);
  }
};

/**
 * Check if a theme is stored
 */
export const hasStoredTheme = (): boolean => {
  return localStorage.getItem(STORAGE_KEY) !== null;
};
