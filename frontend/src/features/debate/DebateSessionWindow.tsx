import { useEffect, useMemo, useState } from "react";
import MenuBar from "../../components/MenuBar";
import { useDebateStore } from "../../state/debateStore";
import { useSendTurn, useScoreDebate } from "../../api/hooks";
import { formatTime } from "../../utils/windowUtils";
import { useDialogStore } from "../../state/dialogStore";
import { useWindowStore } from "../../state/windowStore";
import { useNotificationStore } from "../../state/notificationStore";

const DebateSessionWindow = () => {
  const debate = useDebateStore();
  const { openDialog } = useDialogStore();
  const { openWindow } = useWindowStore();
  const notify = useNotificationStore((state) => state.push);
  const sendTurn = useSendTurn();
  const scoreDebate = useScoreDebate();
  const [input, setInput] = useState("");
  const [speaker, setSpeaker] = useState("");

  useEffect(() => {
    if (!speaker && debate.participants.length > 0) {
      const first = debate.participants.find((p) => p.type === "human");
      if (first) {
        setSpeaker(first.name);
      }
    }
  }, [debate.participants, speaker]);

  useEffect(() => {
    if (debate.sessionStatus !== "active") {
      return;
    }
    const timer = window.setInterval(() => debate.tick(), 1000);
    return () => window.clearInterval(timer);
  }, [debate.sessionStatus, debate.tick]);

  const canSend = input.trim().length > 0 && debate.sessionStatus === "active";

  const handleSend = async () => {
    if (!canSend || !debate.debateId) {
      return;
    }
    const messageId = Math.random().toString(36).slice(2, 10);
    const userMessage = {
      id: messageId,
      role: speaker || debate.participants[0]?.name || "User",
      content: input.trim(),
      timestamp: new Date().toISOString()
    };
    debate.addMessage(userMessage);
    setInput("");
    try {
      const response = await sendTurn.mutateAsync({
        debateId: debate.debateId,
        message: userMessage.content,
        role: userMessage.role
      });
      debate.setLiveScore(messageId, response.updatedScores);
      debate.updateCombo(response.updatedScores);
      debate.addMessage({
        id: Math.random().toString(36).slice(2, 10),
        role: "AI Opponent",
        content: response.aiMessage,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      notify({
        type: "error",
        title: "Turn Failed",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  };

  const handleScore = async () => {
    if (!debate.debateId) {
      return;
    }
    try {
      const result = await scoreDebate.mutateAsync({ debateId: debate.debateId });
      debate.endSession({
        finalScore: result.finalScore,
        breakdown: result.breakdown,
        achievementsUnlocked: result.achievementsUnlocked ?? []
      });
      openWindow("match-results");
    } catch (error) {
      notify({
        type: "error",
        title: "Scoring Failed",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  };

  const handleForfeit = () => {
    openDialog({
      title: "Confirm Forfeit",
      message: "Do you want to forfeit this debate?",
      actions: [
        { label: "Cancel", onClick: () => undefined },
        {
          label: "Forfeit",
          onClick: () => {
            debate.endSession({
              finalScore: 0,
              breakdown: {
                argumentStrength: 0,
                evidenceUse: 0,
                civility: 0,
                relevance: 0
              },
              achievementsUnlocked: []
            });
            openWindow("match-results");
          }
        }
      ]
    });
  };

  const stats = useMemo(
    () => ({
      combo: debate.combo,
      best: debate.streakBest
    }),
    [debate.combo, debate.streakBest]
  );

  if (debate.sessionStatus === "idle") {
    return (
      <div>
        <MenuBar items={["File", "Edit", "View", "Help"]} />
        <p>No active debate. Start a new debate to begin.</p>
      </div>
    );
  }

  return (
    <div>
      <MenuBar items={["File", "Edit", "View", "Help"]} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <strong>{debate.topicTitle || "No topic selected"}</strong>
          <div>Stance: {debate.stance.toUpperCase()}</div>
        </div>
        <div className="timer">Time: {formatTime(debate.timeRemaining)}</div>
      </div>

      <div className="transcript" aria-live="polite">
        {debate.transcript.map((message) => (
          <div key={message.id} className="transcript-message">
            <strong>{message.role}</strong>
            <div>{message.content}</div>
            {message.scores && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 4 }}>
                <span>Argument: {message.scores.argumentStrength}</span>
                <span>Evidence: {message.scores.evidenceUse}</span>
                <span>Civility: {message.scores.civility}</span>
                <span>Relevance: {message.scores.relevance}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {debate.participants.filter((p) => p.type === "human").length > 1 && (
        <div className="field-row" style={{ marginTop: 8 }}>
          <label>
            Speaker
            <select value={speaker} onChange={(event) => setSpeaker(event.target.value)}>
              {debate.participants
                .filter((p) => p.type === "human")
                .map((participant) => (
                  <option key={participant.name} value={participant.name}>
                    {participant.name}
                  </option>
                ))}
            </select>
          </label>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <textarea
          style={{ flex: 1 }}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          rows={3}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          aria-label="Debate input"
        />
        <button type="button" onClick={handleSend} disabled={!canSend}>
          Send
        </button>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <div>
          <strong>Combo:</strong> {stats.combo} | <strong>Best:</strong> {stats.best}
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button type="button" onClick={() => debate.setPaused(!debate.isPaused)}>
            {debate.isPaused ? "Resume" : "Pause"}
          </button>
          <button type="button" onClick={handleForfeit}>Forfeit</button>
          <button type="button" onClick={handleScore} disabled={scoreDebate.isPending}>
            End & Score
          </button>
        </div>
      </div>
    </div>
  );
};

export default DebateSessionWindow;
