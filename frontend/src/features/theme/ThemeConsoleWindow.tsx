/**
 * Theme Console - AI-powered theme generator
 *
 * Allows users to type natural language instructions
 * and generates validated theme tokens via the Theme Agent.
 */

import { useState, useCallback } from "react";
import type { AiTheme, AgentResponse } from "../../api/types";
import MenuBar from "../../components/MenuBar";
import {
  previewTheme,
  applyAndPersist,
  resetTheme,
  loadTheme,
  getDefaultTheme
} from "../../theme";

type Status = "idle" | "loading" | "success" | "error";

const ThemeConsoleWindow = () => {
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [currentTheme, setCurrentTheme] = useState<AiTheme | null>(
    loadTheme() ?? null
  );
  const [previewingTheme, setPreviewingTheme] = useState<AiTheme | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  const getApiBaseUrl = useCallback(() => {
    // Theme agent is on TypeScript API (port 4000), debates are on Python API (port 8000)
    return "http://localhost:4000";
  }, []);

  const generateTheme = useCallback(async () => {
    if (!prompt.trim()) return;

    setStatus("loading");
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/agents/theme`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input: prompt.trim(),
          context: { app: "debate-simulator", uiStyle: "win98" }
        })
      });

      if (!response.ok) {
        setStatus("error");
        setError(`HTTP error ${response.status}: ${response.statusText}`);
        return;
      }

      const result: AgentResponse = await response.json();

      if (!result.ok) {
        setStatus("error");
        setError(result.error?.message || "Theme generation failed");
        return;
      }

      const theme = result.data as AiTheme;
      setPreviewingTheme(theme);
      previewTheme(theme);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Failed to generate theme");
    }
  }, [prompt, getApiBaseUrl]);

  const handleApply = useCallback(() => {
    if (previewingTheme) {
      applyAndPersist(previewingTheme);
      setCurrentTheme(previewingTheme);
      setPreviewingTheme(null);
    }
  }, [previewingTheme]);

  const handleReset = useCallback(() => {
    resetTheme();
    setCurrentTheme(null);
    setPreviewingTheme(null);
    setPrompt("");
    setStatus("idle");
    setError(null);
  }, []);

  const handleCancelPreview = useCallback(() => {
    setPreviewingTheme(null);
    // Restore current theme or clear
    if (currentTheme) {
      previewTheme(currentTheme);
    } else {
      resetTheme();
    }
  }, [currentTheme]);

  const displayTheme = previewingTheme ?? currentTheme ?? getDefaultTheme();

  return (
    <div>
      <MenuBar items={["File", "Edit", "Help"]} />

      <fieldset>
        <legend>Theme Instruction</legend>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., make it more Mario-like, or give me a cyberpunk vibe"
          rows={3}
          style={{ width: "100%", resize: "vertical", fontFamily: "inherit" }}
          disabled={status === "loading"}
        />
        <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
          <button onClick={generateTheme} disabled={status === "loading" || !prompt.trim()}>
            {status === "loading" ? "Generating..." : "Generate"}
          </button>
          {previewingTheme && (
            <>
              <button onClick={handleApply}>Apply</button>
              <button onClick={handleCancelPreview}>Cancel</button>
            </>
          )}
          <button onClick={handleReset} disabled={status === "loading"}>
            Reset
          </button>
        </div>
      </fieldset>

      {error && (
        <fieldset style={{ borderColor: "#c00" }}>
          <legend style={{ color: "#c00" }}>Error</legend>
          <p style={{ margin: 0, color: "#c00" }}>{error}</p>
        </fieldset>
      )}

      <fieldset>
        <legend>
          Current Theme: {displayTheme.name}
          {previewingTheme && " (Preview)"}
        </legend>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <div>
            <strong>Font:</strong> {displayTheme.tokens.fontFamily}
          </div>
          <div>
            <strong>Size:</strong> {displayTheme.tokens.fontSizeBasePx}px
          </div>
          <div>
            <strong>Background:</strong>{" "}
            <span
              style={{
                display: "inline-block",
                width: 14,
                height: 14,
                backgroundColor: displayTheme.tokens.bg,
                border: "1px solid #000",
                verticalAlign: "middle"
              }}
            />{" "}
            {displayTheme.tokens.bg}
          </div>
          <div>
            <strong>Primary:</strong>{" "}
            <span
              style={{
                display: "inline-block",
                width: 14,
                height: 14,
                backgroundColor: displayTheme.tokens.primary,
                border: "1px solid #000",
                verticalAlign: "middle"
              }}
            />{" "}
            {displayTheme.tokens.primary}
          </div>
          <div>
            <strong>Radius:</strong> {displayTheme.tokens.radiusPx}px
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend>
          <label style={{ cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showDebug}
              onChange={(e) => setShowDebug(e.target.checked)}
            />{" "}
            Debug JSON
          </label>
        </legend>
        {showDebug && (
          <pre
            style={{
              margin: 0,
              padding: 8,
              background: "#1a1a1a",
              color: "#0f0",
              fontSize: 11,
              maxHeight: 150,
              overflow: "auto",
              whiteSpace: "pre-wrap",
              wordBreak: "break-all"
            }}
          >
            {JSON.stringify(displayTheme, null, 2)}
          </pre>
        )}
      </fieldset>
    </div>
  );
};

export default ThemeConsoleWindow;
