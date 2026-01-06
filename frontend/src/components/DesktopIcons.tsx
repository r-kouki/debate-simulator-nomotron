import Icon from "./Icon";
import { useWindowStore } from "../state/windowStore";

const icons = [
  { id: "new-debate", label: "New Debate", icon: "debate" },
  { id: "topic-explorer", label: "Topic Explorer", icon: "search" },
  { id: "scoreboard", label: "Scoreboard", icon: "score" },
  { id: "leaderboard", label: "Leaderboard", icon: "trophy" },
  { id: "settings", label: "Settings", icon: "gear" },
  { id: "help", label: "Help", icon: "help" }
] as const;

const DesktopIcons = () => {
  const { openWindow } = useWindowStore();

  return (
    <div className="desktop-icons">
      {icons.map((item) => (
        <div key={item.id} className="desktop-icon">
          <button
            type="button"
            onDoubleClick={() => openWindow(item.id)}
            aria-label={`Open ${item.label}`}
          >
            <Icon name={item.icon} />
            <div>{item.label}</div>
          </button>
        </div>
      ))}
    </div>
  );
};

export default DesktopIcons;
