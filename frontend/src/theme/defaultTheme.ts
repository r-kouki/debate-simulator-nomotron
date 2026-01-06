/**
 * Default Win98-style theme
 * Matches the existing CSS variables in styles/index.css
 */

import type { AiTheme } from "../api/types";

export const defaultTheme: AiTheme = {
  name: "Classic Win98",
  tokens: {
    fontFamily: "Tahoma",
    fontSizeBasePx: 14,
    bg: "#5f9ea0",        // Desktop teal
    panel: "#d4d4d4",     // Surface silver
    text: "#2a2a2a",      // Primary text
    mutedText: "#505050", // Secondary text
    primary: "#000080",   // Navy blue accent
    primaryText: "#ffffff",
    border: "#808080",    // Border dark
    radiusPx: 0,          // Sharp corners
    shadow: "2px 2px 0 rgba(0,0,0,0.35)"
  }
};

export const FONT_ALLOWLIST = ["Tahoma", "Verdana", "Arial", "Trebuchet MS", "Courier New"] as const;
