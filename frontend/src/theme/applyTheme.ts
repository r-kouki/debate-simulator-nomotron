/**
 * Theme Application Utilities
 * Applies AI-generated theme tokens as CSS custom properties
 */

import type { AiTheme } from "../api/types";
import { defaultTheme } from "./defaultTheme";
import { saveTheme, clearTheme } from "./storage";

/**
 * Apply theme tokens to CSS custom properties on :root
 */
const setCssVariables = (theme: AiTheme): void => {
  const root = document.documentElement;
  const { tokens } = theme;

  // Font
  root.style.setProperty("--ai-font-family", `"${tokens.fontFamily}", sans-serif`);
  root.style.setProperty("--ai-font-size-base", `${tokens.fontSizeBasePx}px`);

  // Colors
  root.style.setProperty("--ai-bg", tokens.bg);
  root.style.setProperty("--ai-panel", tokens.panel);
  root.style.setProperty("--ai-text", tokens.text);
  root.style.setProperty("--ai-muted-text", tokens.mutedText);
  root.style.setProperty("--ai-primary", tokens.primary);
  root.style.setProperty("--ai-primary-text", tokens.primaryText);
  root.style.setProperty("--ai-border", tokens.border);

  // Shape
  root.style.setProperty("--ai-radius", `${tokens.radiusPx}px`);
  root.style.setProperty("--ai-shadow", tokens.shadow);

  // Enable AI theme mode
  root.setAttribute("data-ai-theme", "active");
};

/**
 * Remove AI theme CSS variables
 */
const clearCssVariables = (): void => {
  const root = document.documentElement;
  const vars = [
    "--ai-font-family",
    "--ai-font-size-base",
    "--ai-bg",
    "--ai-panel",
    "--ai-text",
    "--ai-muted-text",
    "--ai-primary",
    "--ai-primary-text",
    "--ai-border",
    "--ai-radius",
    "--ai-shadow"
  ];

  vars.forEach((v) => root.style.removeProperty(v));
  root.removeAttribute("data-ai-theme");
};

/**
 * Preview theme without persisting (for live preview)
 */
export const previewTheme = (theme: AiTheme): void => {
  setCssVariables(theme);
};

/**
 * Apply theme and persist to localStorage
 */
export const applyAndPersist = (theme: AiTheme): void => {
  setCssVariables(theme);
  saveTheme(theme);
};

/**
 * Reset to default theme and clear localStorage
 */
export const resetTheme = (): void => {
  clearCssVariables();
  clearTheme();
  // Optionally apply default explicitly
  // setCssVariables(defaultTheme);
};

/**
 * Get the default theme
 */
export const getDefaultTheme = (): AiTheme => defaultTheme;
