import { useCallback, useEffect, useState } from "react";
import type { MouseEvent } from "react";
import { useDesktopBounds } from "../utils/useDesktopBounds";
import Taskbar from "./Taskbar";
import StartMenu from "./StartMenu";
import DesktopIcons from "./DesktopIcons";
import WindowManager from "./WindowManager";
import ContextMenu from "./ContextMenu";
import { useUiStore } from "../state/uiStore";
import { useWindowStore } from "../state/windowStore";
import { windowDefinitions, WindowType } from "../state/windowDefinitions";

export type ContextMenuState = {
  x: number;
  y: number;
  visible: boolean;
};

const Desktop = () => {
  const { ref, bounds } = useDesktopBounds();
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    x: 0,
    y: 0,
    visible: false
  });
  const { isStartMenuOpen, setStartMenuOpen } = useUiStore();
  const { openWindow } = useWindowStore();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const target = params.get("window");
    if (target && target in windowDefinitions) {
      openWindow(target as WindowType);
    }
  }, [openWindow]);

  const handleContextMenu = useCallback((event: MouseEvent) => {
    event.preventDefault();
    setContextMenu({ x: event.clientX, y: event.clientY, visible: true });
    setStartMenuOpen(false);
  }, [setStartMenuOpen]);

  const handleCloseMenus = useCallback(() => {
    setContextMenu((state) => ({ ...state, visible: false }));
    setStartMenuOpen(false);
  }, [setStartMenuOpen]);

  return (
    <div className="desktop" onContextMenu={handleContextMenu} onClick={handleCloseMenus}>
      <div className="desktop-area" ref={ref}>
        <DesktopIcons />
        <WindowManager bounds={bounds} />
        {contextMenu.visible && (
          <ContextMenu x={contextMenu.x} y={contextMenu.y} onClose={handleCloseMenus} />
        )}
        {isStartMenuOpen && <StartMenu onClose={handleCloseMenus} />}
      </div>
      <Taskbar />
    </div>
  );
};

export default Desktop;
