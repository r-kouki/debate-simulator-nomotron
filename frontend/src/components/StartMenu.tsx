import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { useWindowStore } from "../state/windowStore";

type MenuItem = {
  label: string;
  action?: () => void;
  children?: MenuItem[];
};

const StartMenu = ({ onClose }: { onClose: () => void }) => {
  const { openWindow } = useWindowStore();
  const menuItems = useMemo<MenuItem[]>(
    () => [
      {
        label: "Programs",
        children: [
          {
            label: "Debate",
            children: [
              { label: "New Debate", action: () => openWindow("new-debate") },
              { label: "Debate Session", action: () => openWindow("debate-session") }
            ]
          },
          { label: "Topic Explorer", action: () => openWindow("topic-explorer") },
          { label: "Scoreboard", action: () => openWindow("scoreboard") },
          { label: "Connection Status", action: () => openWindow("connection-status") }
        ]
      },
      { label: "Settings", action: () => openWindow("settings") },
      { label: "Theme Console", action: () => openWindow("theme-console") },
      { label: "Help", action: () => openWindow("help") },
      { label: "About", action: () => openWindow("about") }
    ],
    [openWindow]
  );

  const [activeIndex, setActiveIndex] = useState(0);
  const [activeSubIndex, setActiveSubIndex] = useState<number | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    menuRef.current?.focus();
  }, []);

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      setActiveIndex((prev) => (prev + 1) % menuItems.length);
      event.preventDefault();
    }
    if (event.key === "ArrowUp") {
      setActiveIndex((prev) => (prev - 1 + menuItems.length) % menuItems.length);
      event.preventDefault();
    }
    if (event.key === "ArrowRight") {
      if (menuItems[activeIndex].children) {
        setActiveSubIndex(0);
      }
    }
    if (event.key === "ArrowLeft") {
      setActiveSubIndex(null);
    }
    if (event.key === "Enter") {
      const item = menuItems[activeIndex];
      if (item.action) {
        item.action();
        onClose();
      }
    }
    if (event.key === "Escape") {
      onClose();
    }
  };

  return (
    <div
      ref={menuRef}
      className="start-menu"
      onKeyDown={handleKeyDown}
      onClick={(event) => event.stopPropagation()}
      tabIndex={0}
    >
      <menu className="menu" role="menu" aria-label="Start menu">
        {menuItems.map((item, index) => (
          <li key={item.label} role="menuitem">
            <button
              className="menu-item"
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => {
                if (item.action) {
                  item.action();
                  onClose();
                }
              }}
              aria-haspopup={Boolean(item.children)}
              type="button"
            >
              {item.label} {item.children ? ">" : ""}
            </button>
            {item.children && activeIndex === index && (
              <menu className="menu" role="menu" style={{ position: "absolute", left: 220, top: index * 26 }}>
                {item.children.map((child, childIndex) => (
                  <li key={child.label} role="menuitem">
                    <button
                      className="menu-item"
                      onMouseEnter={() => setActiveSubIndex(childIndex)}
                      onClick={() => {
                        if (child.action) {
                          child.action();
                          onClose();
                        }
                      }}
                      aria-haspopup={Boolean(child.children)}
                      type="button"
                    >
                      {child.label} {child.children ? ">" : ""}
                    </button>
                    {child.children && activeSubIndex === childIndex && (
                      <menu
                        className="menu"
                        role="menu"
                        style={{ position: "absolute", left: 220, top: childIndex * 26 }}
                      >
                        {child.children.map((grandChild) => (
                          <li key={grandChild.label} role="menuitem">
                            <button
                              className="menu-item"
                              onClick={() => {
                                grandChild.action?.();
                                onClose();
                              }}
                              type="button"
                            >
                              {grandChild.label}
                            </button>
                          </li>
                        ))}
                      </menu>
                    )}
                  </li>
                ))}
              </menu>
            )}
          </li>
        ))}
      </menu>
    </div>
  );
};

export default StartMenu;
