import { useState, useEffect } from "react";
import MenuBar from "../../components/MenuBar";
import { getApiAdapter } from "../../api/adapter";
import type { LeaderboardEntry } from "../../api/types";

type SortOption = "xp" | "wins" | "winRate" | "averageScore";

const LeaderboardWindow = () => {
    const [players, setPlayers] = useState<LeaderboardEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [sortBy, setSortBy] = useState<SortOption>("xp");
    const [page, setPage] = useState(1);
    const [totalPlayers, setTotalPlayers] = useState(0);
    const pageSize = 10;

    const fetchLeaderboard = async () => {
        setLoading(true);
        setError("");
        try {
            const api = getApiAdapter();
            const response = await api.getLeaderboard({ page, pageSize, sortBy });
            setPlayers(response.players);
            setTotalPlayers(response.totalPlayers);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load leaderboard");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLeaderboard();
    }, [page, sortBy]);

    const totalPages = Math.ceil(totalPlayers / pageSize);

    return (
        <div>
            <MenuBar items={["File", "View", "Help"]} />

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    Sort by:
                    <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortOption)}>
                        <option value="xp">XP</option>
                        <option value="wins">Total Wins</option>
                        <option value="winRate">Win Rate</option>
                        <option value="averageScore">Average Score</option>
                    </select>
                </label>
                <button onClick={fetchLeaderboard} disabled={loading}>
                    {loading ? "Loading..." : "Refresh"}
                </button>
            </div>

            {error && (
                <div style={{ color: "#c00", padding: 8, background: "#fee", marginBottom: 8 }}>
                    {error}
                </div>
            )}

            <div className="panel" style={{ maxHeight: 320, overflowY: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ borderBottom: "2px solid #808080" }}>
                            <th style={{ textAlign: "left", padding: "4px 8px" }}>#</th>
                            <th style={{ textAlign: "left", padding: "4px 8px" }}>Player</th>
                            <th style={{ textAlign: "center", padding: "4px 8px" }}>Lvl</th>
                            <th style={{ textAlign: "center", padding: "4px 8px" }}>W/L</th>
                            <th style={{ textAlign: "center", padding: "4px 8px" }}>Win%</th>
                            <th style={{ textAlign: "center", padding: "4px 8px" }}>Avg</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={6} style={{ textAlign: "center", padding: 16 }}>
                                    Loading...
                                </td>
                            </tr>
                        ) : players.length === 0 ? (
                            <tr>
                                <td colSpan={6} style={{ textAlign: "center", padding: 16 }}>
                                    No players found
                                </td>
                            </tr>
                        ) : (
                            players.map((player) => (
                                <tr
                                    key={player.playerId}
                                    style={{
                                        borderBottom: "1px solid #c0c0c0",
                                        background: player.rank <= 3 ? "#ffffdd" : undefined
                                    }}
                                >
                                    <td style={{ padding: "6px 8px", fontWeight: player.rank <= 3 ? "bold" : "normal" }}>
                                        {player.rank === 1 ? "🥇" : player.rank === 2 ? "🥈" : player.rank === 3 ? "🥉" : player.rank}
                                    </td>
                                    <td style={{ padding: "6px 8px" }}>
                                        <span style={{ marginRight: 6 }}>{player.avatar}</span>
                                        <strong>{player.username}</strong>
                                    </td>
                                    <td style={{ textAlign: "center", padding: "6px 8px" }}>{player.level}</td>
                                    <td style={{ textAlign: "center", padding: "6px 8px" }}>
                                        {player.stats.wins}/{player.stats.losses}
                                    </td>
                                    <td style={{ textAlign: "center", padding: "6px 8px" }}>{player.stats.winRate}%</td>
                                    <td style={{ textAlign: "center", padding: "6px 8px" }}>{player.stats.averageScore}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {totalPages > 1 && (
                <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 8 }}>
                    <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1 || loading}>
                        Previous
                    </button>
                    <span style={{ padding: "4px 8px" }}>
                        Page {page} of {totalPages}
                    </span>
                    <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages || loading}>
                        Next
                    </button>
                </div>
            )}

            <fieldset style={{ marginTop: 12 }}>
                <legend>Legend</legend>
                <div style={{ display: "flex", gap: 16, fontSize: 12 }}>
                    <span>🥇 1st Place</span>
                    <span>🥈 2nd Place</span>
                    <span>🥉 3rd Place</span>
                </div>
            </fieldset>
        </div>
    );
};

export default LeaderboardWindow;
