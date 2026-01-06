import { useEffect, useRef } from "react";
import MenuBar from "../../components/MenuBar";
import { useDebateStore } from "../../state/debateStore";
import { useProfileStore } from "../../state/profileStore";
import { useNotificationStore } from "../../state/notificationStore";

const MatchResultsWindow = () => {
  const { matchResult, topicTitle, mode } = useDebateStore();
  const profile = useProfileStore();
  const notify = useNotificationStore((state) => state.push);
  const lastResultId = useRef<string | null>(null);

  useEffect(() => {
    if (!matchResult) {
      return;
    }
    const resultKey = `${matchResult.finalScore}-${topicTitle}-${mode}`;
    if (lastResultId.current === resultKey) {
      return;
    }
    lastResultId.current = resultKey;
    if (matchResult.achievementsUnlocked.length > 0) {
      profile.unlockAchievements(matchResult.achievementsUnlocked);
      notify({
        type: "achievement",
        title: "Achievement Unlocked",
        message: matchResult.achievementsUnlocked.join(", ")
      });
    }
    profile.addMatch({
      id: `match-${Date.now()}`,
      topic: topicTitle || "Untitled",
      mode: mode === "human-vs-ai" ? "Human vs AI" : "Cops vs AI",
      date: new Date().toISOString().split("T")[0],
      score: matchResult.finalScore,
      result: matchResult.finalScore >= 75 ? "Win" : "Loss"
    });
  }, [matchResult, mode, notify, profile, topicTitle]);

  if (!matchResult) {
    return <div>No results yet.</div>;
  }

  return (
    <div>
      <MenuBar items={["File", "View", "Help"]} />
      <h3>Match Results</h3>
      <p>
        Final Score: <strong>{matchResult.finalScore}</strong>
      </p>
      <div className="panel">
        <div>Argument Strength: {matchResult.breakdown.argumentStrength}</div>
        <div>Evidence Use: {matchResult.breakdown.evidenceUse}</div>
        <div>Civility: {matchResult.breakdown.civility}</div>
        <div>Relevance: {matchResult.breakdown.relevance}</div>
      </div>
      <h4>Rewards</h4>
      <div className="xp-bar">
        <div
          className="xp-bar-fill"
          style={{ width: `${(profile.xp / profile.xpNext) * 100}%` }}
        />
      </div>
      <div>XP: {profile.xp} / {profile.xpNext}</div>
      {matchResult.achievementsUnlocked.length > 0 ? (
        <div>Unlocked: {matchResult.achievementsUnlocked.join(", ")}</div>
      ) : (
        <div>No achievements unlocked.</div>
      )}
    </div>
  );
};

export default MatchResultsWindow;
