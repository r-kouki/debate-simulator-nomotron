import { useEffect, useState } from "react";
import MenuBar from "../../components/MenuBar";
import Icon, { IconName } from "../../components/Icon";
import { useProfile, useUpdateProfile } from "../../api/hooks";
import { useProfileStore } from "../../state/profileStore";
import { useSettingsStore } from "../../state/settingsStore";

const avatarOptions: IconName[] = ["profile", "trophy", "debate", "chat", "search"];

const ScoreboardWindow = () => {
  const profileQuery = useProfile();
  const updateProfile = useUpdateProfile();
  const profileStore = useProfileStore();
  const settings = useSettingsStore();
  const [username, setUsername] = useState(profileStore.username);
  const [avatar, setAvatar] = useState<IconName>(profileStore.avatar as IconName);

  useEffect(() => {
    if (profileQuery.data) {
      profileStore.setProfile(profileQuery.data);
      setUsername(profileQuery.data.username);
      setAvatar(profileQuery.data.avatar as IconName);
    }
  }, [profileQuery.data, profileStore]);

  const handleSave = async () => {
    await updateProfile.mutateAsync({ username, avatar });
    profileStore.setProfile({ username, avatar });
    settings.setUsername(username);
  };

  const stats = profileStore.stats || {
    wins: 0,
    losses: 0,
    winRate: 0,
    averageScore: 0,
    bestStreak: 0,
    topicsPlayed: 0,
  };
  const achievements = profileStore.achievements || [];
  const history = profileStore.history || [];

  return (
    <div>
      <MenuBar items={["File", "View", "Help"]} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 8 }}>
        <div className="panel">
          <h3>Player Profile</h3>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <Icon name={avatar} />
            <div>
              <div>
                <strong>{profileStore.rankTitle}</strong>
              </div>
              <div>Level {profileStore.level}</div>
            </div>
          </div>
          <div className="xp-bar" style={{ marginTop: 6 }}>
            <div
              className="xp-bar-fill"
              style={{ width: `${(profileStore.xp / profileStore.xpNext) * 100}%` }}
            />
          </div>
          <div>XP {profileStore.xp} / {profileStore.xpNext}</div>
          <div className="field-row-stacked">
            <label>
              Username
              <input value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>
          </div>
          <div>
            Avatar
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {avatarOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setAvatar(option)}
                  aria-label={`Avatar ${option}`}
                >
                  <Icon name={option} />
                </button>
              ))}
            </div>
          </div>
          <button type="button" onClick={handleSave} disabled={updateProfile.isPending}>
            Save Profile
          </button>
        </div>
        <div className="panel">
          <h3>Statistics</h3>
          <div>Wins: {stats.wins}</div>
          <div>Losses: {stats.losses}</div>
          <div>Win Rate: {stats.winRate}%</div>
          <div>Average Score: {stats.averageScore}</div>
          <div>Best Streak: {stats.bestStreak}</div>
          <div>Topics Played: {stats.topicsPlayed}</div>
          <h3>Achievements</h3>
          <ul>
            {achievements.map((achievement) => (
              <li key={achievement.id}>
                {achievement.unlocked ? "[Unlocked]" : "[Locked]"} {achievement.title} -
                {achievement.description}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="panel" style={{ marginTop: 8 }}>
        <h3>Match History</h3>
        {history.map((match) => (
          <div key={match.id} style={{ display: "flex", justifyContent: "space-between" }}>
            <span>{match.date}</span>
            <span>{match.topic}</span>
            <span>{match.mode}</span>
            <span>{match.score}</span>
            <span>{match.result}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScoreboardWindow;
