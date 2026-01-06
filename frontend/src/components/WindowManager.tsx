import { windowDefinitions, WindowType } from "../state/windowDefinitions";
import { useWindowStore } from "../state/windowStore";
import WindowFrame from "./WindowFrame";
import type { Rect } from "../utils/windowUtils";
import type { ComponentType } from "react";
import AboutWindow from "../features/settings/AboutWindow";
import HelpWindow from "../features/settings/HelpWindow";
import SettingsWindow from "../features/settings/SettingsWindow";
import ConnectionStatusWindow from "../features/settings/ConnectionStatusWindow";
import NewDebateWindow from "../features/debate/NewDebateWindow";
import DebateSessionWindow from "../features/debate/DebateSessionWindow";
import MatchResultsWindow from "../features/debate/MatchResultsWindow";
import TopicExplorerWindow from "../features/topics/TopicExplorerWindow";
import ScoreboardWindow from "../features/profile/ScoreboardWindow";
import LoginWindow from "../features/auth/LoginWindow";
import LeaderboardWindow from "../features/leaderboard/LeaderboardWindow";
import ThemeConsoleWindow from "../features/theme/ThemeConsoleWindow";

const windowComponents: Record<WindowType, ComponentType> = {
  "new-debate": NewDebateWindow,
  "debate-session": DebateSessionWindow,
  "match-results": MatchResultsWindow,
  "topic-explorer": TopicExplorerWindow,
  scoreboard: ScoreboardWindow,
  settings: SettingsWindow,
  help: HelpWindow,
  about: AboutWindow,
  "connection-status": ConnectionStatusWindow,
  login: LoginWindow,
  leaderboard: LeaderboardWindow,
  "theme-console": ThemeConsoleWindow
};

const WindowManager = ({ bounds }: { bounds: Rect }) => {
  const { windows } = useWindowStore();

  return (
    <>
      {Object.values(windows).map((windowState) => {
        if (!windowState.isOpen) {
          return null;
        }
        const definition = windowDefinitions[windowState.id];
        const Component = windowComponents[windowState.id];
        return (
          <WindowFrame
            key={windowState.id}
            windowState={windowState}
            bounds={bounds}
            icon={definition.icon}
          >
            <Component />
          </WindowFrame>
        );
      })}
    </>
  );
};

export default WindowManager;
