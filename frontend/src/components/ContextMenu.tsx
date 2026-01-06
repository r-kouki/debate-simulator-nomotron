import { useWindowStore } from "../state/windowStore";

const ContextMenu = ({ x, y, onClose }: { x: number; y: number; onClose: () => void }) => {
  const { openWindow } = useWindowStore();

  const handleAction = (action: () => void) => {
    action();
    onClose();
  };

  return (
    <div
      className="context-menu"
      style={{ left: x, top: y }}
      onClick={(event) => event.stopPropagation()}
    >
      <menu className="menu" role="menu">
        <li role="menuitem">
          <button type="button" onClick={onClose}>Arrange Icons</button>
        </li>
        <li role="menuitem">
          <button type="button" onClick={() => handleAction(() => openWindow("new-debate"))}>
            New Debate
          </button>
        </li>
        <li role="menuitem">
          <button type="button" onClick={() => handleAction(() => openWindow("topic-explorer"))}>
            Topic Explorer
          </button>
        </li>
        <li role="menuitem">
          <button type="button" onClick={() => handleAction(() => openWindow("settings"))}>
            Settings
          </button>
        </li>
        <li role="menuitem">
          <button type="button" onClick={() => handleAction(() => openWindow("about"))}>
            About
          </button>
        </li>
        <li role="menuitem">
          <button type="button" onClick={onClose}>Refresh</button>
        </li>
      </menu>
    </div>
  );
};

export default ContextMenu;
