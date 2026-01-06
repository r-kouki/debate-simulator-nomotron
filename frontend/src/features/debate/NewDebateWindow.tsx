import { useEffect, useState } from "react";
import MenuBar from "../../components/MenuBar";
import { useSettingsStore } from "../../state/settingsStore";
import { useDebateStore } from "../../state/debateStore";
import { useStartDebate } from "../../api/hooks";
import { useWindowStore } from "../../state/windowStore";
import { useNotificationStore } from "../../state/notificationStore";

const NewDebateWindow = () => {
  const settings = useSettingsStore();
  const debate = useDebateStore();
  const { openWindow, closeWindow } = useWindowStore();
  const startDebate = useStartDebate();
  const notify = useNotificationStore((state) => state.push);

  const [mode, setMode] = useState(debate.mode);
  const [topicTitle, setTopicTitle] = useState(debate.topicTitle || "AI in Education");
  const [stance, setStance] = useState(debate.stance);
  const [difficulty, setDifficulty] = useState(debate.difficulty || settings.difficultyDefault);
  const [timerSeconds, setTimerSeconds] = useState(debate.timerSeconds || settings.timerSeconds);
  const [cop1, setCop1] = useState(settings.username);
  const [cop2, setCop2] = useState("Partner");

  useEffect(() => {
    if (debate.topicTitle) {
      setTopicTitle(debate.topicTitle);
    }
  }, [debate.topicTitle]);

  const handleStart = async () => {
    const participants =
      mode === "cops-vs-ai"
        ? [
            { name: cop1, type: "human" as const },
            { name: cop2, type: "human" as const }
          ]
        : [{ name: settings.username, type: "human" as const }];

    const payload = {
      topicId: debate.topicId,
      topicTitle,
      stance,
      mode,
      difficulty,
      participants: [...participants, { name: "AI Opponent", type: "ai" as const }],
      timerSeconds
    };

    try {
      const response = await startDebate.mutateAsync(payload);
      debate.configure({ mode, topicTitle, stance, difficulty, timerSeconds });
      debate.setParticipants(payload.participants);
      debate.startSession(response.debateId, timerSeconds);
      openWindow("debate-session");
      closeWindow("new-debate");
      notify({
        type: "success",
        title: "Debate Started",
        message: `Match ID ${response.debateId}`
      });
    } catch (error) {
      notify({
        type: "error",
        title: "Failed to start",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  };

  return (
    <div>
      <MenuBar items={["File", "Edit", "View", "Help"]} />
      <fieldset>
        <legend>Mode</legend>
        <label>
          <input
            type="radio"
            name="mode"
            checked={mode === "human-vs-ai"}
            onChange={() => setMode("human-vs-ai")}
          />
          Human vs AI
        </label>
        <label>
          <input
            type="radio"
            name="mode"
            checked={mode === "cops-vs-ai"}
            onChange={() => setMode("cops-vs-ai")}
          />
          Cops vs AI (2 humans)
        </label>
        <label>
          <input
            type="radio"
            name="mode"
            checked={mode === "ai-vs-ai"}
            onChange={() => setMode("ai-vs-ai")}
          />
          AI vs AI (Spectator)
        </label>
      </fieldset>

      {mode === "cops-vs-ai" && (
        <fieldset>
          <legend>Participants</legend>
          <div className="field-row-stacked">
            <label>
              Cop 1
              <input value={cop1} onChange={(event) => setCop1(event.target.value)} />
            </label>
          </div>
          <div className="field-row-stacked">
            <label>
              Cop 2
              <input value={cop2} onChange={(event) => setCop2(event.target.value)} />
            </label>
          </div>
        </fieldset>
      )}

      <fieldset>
        <legend>Topic</legend>
        <div className="field-row-stacked">
          <label>
            Debate Topic
            <input value={topicTitle} onChange={(event) => setTopicTitle(event.target.value)} />
          </label>
        </div>
        <button type="button" onClick={() => openWindow("topic-explorer")}>
          Open Topic Explorer
        </button>
      </fieldset>

      <fieldset>
        <legend>Rules</legend>
        <div className="field-row">
          <label>
            Stance
            <select value={stance} onChange={(event) => setStance(event.target.value as typeof stance)}>
              <option value="pro">Pro</option>
              <option value="con">Con</option>
              <option value="neutral">Neutral</option>
            </select>
          </label>
          <label>
            Difficulty
            <select
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value as typeof difficulty)}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </label>
        </div>
        <label>
          Round Timer (seconds)
          <input
            type="number"
            min={60}
            max={900}
            value={timerSeconds}
            onChange={(event) => setTimerSeconds(Number(event.target.value))}
          />
        </label>
      </fieldset>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <button type="button" onClick={() => closeWindow("new-debate")}>Cancel</button>
        <button type="button" onClick={handleStart} disabled={startDebate.isPending}>
          {startDebate.isPending ? "Starting..." : "Start Debate"}
        </button>
      </div>
    </div>
  );
};

export default NewDebateWindow;
