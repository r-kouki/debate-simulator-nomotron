import MenuBar from "../../components/MenuBar";
import { useSettingsStore } from "../../state/settingsStore";
import { useThemeStore } from "../../state/themeStore";

const SettingsWindow = () => {
  const settings = useSettingsStore();
  const { theme, setTheme } = useThemeStore();

  return (
    <div>
      <MenuBar items={["File", "Edit", "View", "Help"]} />
      <fieldset>
        <legend>Display</legend>
        <label>
          Theme
          <select
            value={theme}
            onChange={(event) => setTheme(event.target.value as "light" | "dark")}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </fieldset>
      <fieldset>
        <legend>Profile</legend>
        <label>
          Username
          <input value={settings.username} onChange={(event) => settings.setUsername(event.target.value)} />
        </label>
      </fieldset>
      <fieldset>
        <legend>Gameplay</legend>
        <label>
          Sound
          <select
            value={settings.soundEnabled ? "on" : "off"}
            onChange={(event) => settings.setSoundEnabled(event.target.value === "on")}
          >
            <option value="on">On</option>
            <option value="off">Off</option>
          </select>
        </label>
        <label>
          Default Difficulty
          <select
            value={settings.difficultyDefault}
            onChange={(event) => settings.setDifficultyDefault(event.target.value as typeof settings.difficultyDefault)}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
        <label>
          Timer Default (seconds)
          <input
            type="number"
            value={settings.timerSeconds}
            min={60}
            max={900}
            onChange={(event) => settings.setTimerSeconds(Number(event.target.value))}
          />
        </label>
      </fieldset>
      <fieldset>
        <legend>API</legend>
        <label>
          Base URL Override
          <input
            placeholder="https://api.example.com"
            value={settings.apiBaseUrlOverride}
            onChange={(event) => settings.setApiBaseUrlOverride(event.target.value)}
          />
        </label>
        <label>
          Mock Mode
          <select
            value={settings.useMocks ? "true" : "false"}
            onChange={(event) => settings.setUseMocks(event.target.value === "true")}
          >
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>
        </label>
      </fieldset>
    </div>
  );
};

export default SettingsWindow;
