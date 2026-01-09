import { useCallback, useRef, useState } from 'react';
import Draggable, { DraggableEvent, DraggableData } from 'react-draggable';
import { ResizableBox, ResizeCallbackData } from 'react-resizable';
import { WindowState } from '@/types';
import { useWindowStore, useSettingsStore } from '@/stores';
import { TitleBar } from './TitleBar';
import 'react-resizable/css/styles.css';

interface WindowProps {
  window: WindowState;
  children: React.ReactNode;
}

export const Window: React.FC<WindowProps> = ({ window: windowState, children }) => {
  const nodeRef = useRef<HTMLDivElement>(null);
  const { focusWindow, updateWindowPosition, updateWindowSize, closeWindow } = useWindowStore();
  const { settings } = useSettingsStore();
  const [isClosing, setIsClosing] = useState(false);

  const handleDragStart = useCallback(() => {
    focusWindow(windowState.id);
  }, [focusWindow, windowState.id]);

  const handleDrag = useCallback(
    (_e: DraggableEvent, data: DraggableData) => {
      updateWindowPosition(windowState.id, { x: data.x, y: data.y });
    },
    [updateWindowPosition, windowState.id]
  );

  const handleResize = useCallback(
    (_e: React.SyntheticEvent, data: ResizeCallbackData) => {
      updateWindowSize(windowState.id, { width: data.size.width, height: data.size.height });
    },
    [updateWindowSize, windowState.id]
  );

  const handleClose = useCallback(() => {
    if (settings.windowAnimation) {
      setIsClosing(true);
      setTimeout(() => closeWindow(windowState.id), 150);
    } else {
      closeWindow(windowState.id);
    }
  }, [closeWindow, windowState.id, settings.windowAnimation]);

  const handleMouseDown = useCallback(() => {
    if (!windowState.isFocused) {
      focusWindow(windowState.id);
    }
  }, [focusWindow, windowState.id, windowState.isFocused]);

  if (windowState.isMinimized) {
    return null;
  }

  const windowContent = (
    <div
      ref={nodeRef}
      className={`absolute ${isClosing ? 'window-close' : settings.windowAnimation ? 'window-open' : ''}`}
      style={{
        zIndex: windowState.zIndex,
        left: windowState.isMaximized ? 0 : undefined,
        top: windowState.isMaximized ? 0 : undefined,
        width: windowState.isMaximized ? '100%' : undefined,
        height: windowState.isMaximized ? 'calc(100% - 36px)' : undefined,
      }}
      onMouseDown={handleMouseDown}
    >
      <div
        className="flex flex-col bg-xp-gray rounded-t-lg shadow-xp overflow-hidden"
        style={{
          width: windowState.isMaximized ? '100%' : windowState.size.width,
          height: windowState.isMaximized ? '100%' : windowState.size.height,
        }}
      >
        <TitleBar
          title={windowState.title}
          icon={windowState.icon}
          isFocused={windowState.isFocused}
          isMaximized={windowState.isMaximized}
          windowId={windowState.id}
          onClose={handleClose}
        />
        <div className="flex-1 overflow-auto bg-xp-gray border-x-2 border-b-2 border-[#0054E3]">
          {children}
        </div>
      </div>
    </div>
  );

  if (windowState.isMaximized) {
    return windowContent;
  }

  return (
    <Draggable
      nodeRef={nodeRef}
      handle=".window-drag-handle"
      position={windowState.position}
      onStart={handleDragStart}
      onDrag={handleDrag}
      bounds="parent"
    >
      {windowState.resizable !== false ? (
        <ResizableBox
          width={windowState.size.width}
          height={windowState.size.height}
          minConstraints={[
            windowState.minSize?.width || 300,
            windowState.minSize?.height || 200,
          ]}
          maxConstraints={
            windowState.maxSize
              ? [windowState.maxSize.width, windowState.maxSize.height]
              : undefined
          }
          onResize={handleResize}
          resizeHandles={['se', 'e', 's']}
        >
          {windowContent}
        </ResizableBox>
      ) : (
        windowContent
      )}
    </Draggable>
  );
};
