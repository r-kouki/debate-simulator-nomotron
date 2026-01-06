import { useEffect, useMemo, useState } from "react";
import { useUiStore } from "../state/uiStore";
import { useWindowStore } from "../state/windowStore";
import type { WindowType } from "../state/windowDefinitions";
import Icon from "./Icon";
import { useApiStatusStore } from "../state/apiStatusStore";
import { useHealth } from "../api/hooks";

const Taskbar = () => {
  const { toggleStartMenu } = useUiStore();
  const { windows, focusWindow, minimizeWindow } = useWindowStore();
  const { online } = useApiStatusStore();
  const [clock, setClock] = useState(() => new Date());
  useHealth();

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const openWindows = useMemo(
    () => Object.values(windows).filter((win) => win.isOpen),
    [windows]
  );

  const activeWindow = useMemo(() => {
    return openWindows.reduce(
      (current, win) => (win.zIndex > current.zIndex && !win.isMinimized ? win : current),
      { zIndex: 0 } as { zIndex: number; id?: string }
    );
  }, [openWindows]);

  const handleTaskClick = (id: WindowType) => {
    const win = windows[id];
    if (!win) {
      return;
    }
    if (win.isMinimized || activeWindow.id !== id) {
      focusWindow(id);
    } else {
      minimizeWindow(id);
    }
  };

  return (
    <div className="taskbar" onClick={(event) => event.stopPropagation()}>
      <button
        className="start-button"
        type="button"
        onClick={toggleStartMenu}
        aria-label="Open Start menu"
      >
        <Icon name="profile" /> Start
      </button>
      <div className="task-list">
        {openWindows.map((win) => (
          <button
            key={win.id}
            className="task-button"
            onClick={() => handleTaskClick(win.id)}
            aria-label={`Focus ${win.title}`}
            aria-pressed={activeWindow.id === win.id && !win.isMinimized}
          >
            {win.title}
          </button>
        ))}
      </div>
      <div className="tray">
        <span className="status-pill">{online ? "Online" : "Offline"}</span>
        <span>{clock.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
      </div>
    </div>
  );
};

export default Taskbar;
