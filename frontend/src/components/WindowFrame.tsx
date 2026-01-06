import { Rnd } from "react-rnd";
import type { ReactNode } from "react";
import { clampRectToBounds, Rect } from "../utils/windowUtils";
import { useWindowStore, WindowState } from "../state/windowStore";
import Icon from "./Icon";
import { useDebateStore } from "../state/debateStore";
import { useDialogStore } from "../state/dialogStore";

const WindowFrame = ({
  windowState,
  bounds,
  icon,
  children
}: {
  windowState: WindowState;
  bounds: Rect;
  icon: Parameters<typeof Icon>[0]["name"];
  children: ReactNode;
}) => {
  const { minimizeWindow, closeWindow, focusWindow, setWindowRect, toggleMaximize } =
    useWindowStore();
  const sessionStatus = useDebateStore((state) => state.sessionStatus);
  const { openDialog } = useDialogStore();

  const handleDragStop = (_: unknown, data: { x: number; y: number }) => {
    const next = clampRectToBounds(
      {
        x: data.x,
        y: data.y,
        width: windowState.rect.width,
        height: windowState.rect.height
      },
      bounds
    );
    setWindowRect(windowState.id, next);
  };

  const handleResizeStop = (
    _: unknown,
    __: unknown,
    ref: HTMLElement,
    ___: unknown,
    position: { x: number; y: number }
  ) => {
    const next = clampRectToBounds(
      {
        x: position.x,
        y: position.y,
        width: ref.offsetWidth,
        height: ref.offsetHeight
      },
      bounds
    );
    setWindowRect(windowState.id, next);
  };

  const style = windowState.isMinimized ? { display: "none" } : undefined;

  return (
    <Rnd
      style={{ zIndex: windowState.zIndex, position: "absolute", ...style }}
      size={{ width: windowState.rect.width, height: windowState.rect.height }}
      position={{ x: windowState.rect.x, y: windowState.rect.y }}
      bounds="parent"
      disableDragging={windowState.isMaximized}
      enableResizing={!windowState.isMaximized}
      onDragStart={() => focusWindow(windowState.id)}
      onDragStop={handleDragStop}
      onResizeStart={() => focusWindow(windowState.id)}
      onResizeStop={handleResizeStop}
      onMouseDown={() => focusWindow(windowState.id)}
    >
      <div className="window" style={{ height: "100%" }}>
        <div className="title-bar">
          <div className="title-bar-text window-header-title">
            <Icon name={icon} />
            {windowState.title}
          </div>
          <div className="title-bar-controls">
            <button
              type="button"
              aria-label="Minimize"
              onClick={() => minimizeWindow(windowState.id)}
            />
            <button
              aria-label={windowState.isMaximized ? "Restore" : "Maximize"}
              onClick={() => toggleMaximize(windowState.id, bounds)}
              type="button"
            />
            <button
              aria-label="Close"
              onClick={() => {
                if (windowState.id === "debate-session" && sessionStatus === "active") {
                  openDialog({
                    title: "Confirm Exit Debate",
                    message: "Exit the debate session? Your progress will be lost.",
                    actions: [
                      { label: "Stay", onClick: () => undefined },
                      { label: "Exit", onClick: () => closeWindow(windowState.id) }
                    ]
                  });
                } else {
                  closeWindow(windowState.id);
                }
              }}
              type="button"
            />
          </div>
        </div>
        <div className="window-body" style={{ height: "calc(100% - 30px)" }}>
          {children}
        </div>
      </div>
    </Rnd>
  );
};

export default WindowFrame;
