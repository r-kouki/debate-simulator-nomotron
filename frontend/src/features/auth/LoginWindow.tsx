import { useState } from "react";
import MenuBar from "../../components/MenuBar";
import { useLogin, useRegister } from "../../api/hooks/useAuth";
import { useAuthStore } from "../../state/authStore";
import { useWindowStore } from "../../state/windowStore";

const LoginWindow = () => {
    const [tab, setTab] = useState<"login" | "register">("login");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");

    const { isAuthenticated, user, logout } = useAuthStore();
    const { closeWindow } = useWindowStore();
    const loginMutation = useLogin();
    const registerMutation = useRegister();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        try {
            await loginMutation.mutateAsync({ username, password });
            closeWindow("login");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        try {
            await registerMutation.mutateAsync({ username, password });
            closeWindow("login");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Registration failed");
        }
    };

    const handleLogout = () => {
        logout();
        setUsername("");
        setPassword("");
        setConfirmPassword("");
    };

    if (isAuthenticated && user) {
        return (
            <div>
                <MenuBar items={["File", "Help"]} />
                <fieldset>
                    <legend>Logged In</legend>
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Player ID:</strong> {user.playerId.slice(0, 8)}...</p>
                    <p><strong>Member since:</strong> {new Date(user.createdAt).toLocaleDateString()}</p>
                    <button onClick={handleLogout} style={{ marginTop: 8 }}>Log Out</button>
                </fieldset>
            </div>
        );
    }

    return (
        <div>
            <MenuBar items={["File", "Help"]} />
            <div className="tabs">
                <button
                    className={tab === "login" ? "" : undefined}
                    onClick={() => setTab("login")}
                    style={{ fontWeight: tab === "login" ? "bold" : "normal" }}
                >
                    Login
                </button>
                <button
                    className={tab === "register" ? "" : undefined}
                    onClick={() => setTab("register")}
                    style={{ fontWeight: tab === "register" ? "bold" : "normal" }}
                >
                    Register
                </button>
            </div>

            {error && (
                <div style={{ color: "#c00", marginBottom: 8, padding: 4, background: "#fee" }}>
                    {error}
                </div>
            )}

            {tab === "login" ? (
                <form onSubmit={handleLogin}>
                    <fieldset>
                        <legend>Sign In</legend>
                        <label>
                            Username
                            <input
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                minLength={3}
                            />
                        </label>
                        <label>
                            Password
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                            />
                        </label>
                        <button type="submit" disabled={loginMutation.isPending} style={{ marginTop: 8 }}>
                            {loginMutation.isPending ? "Logging in..." : "Login"}
                        </button>
                    </fieldset>
                </form>
            ) : (
                <form onSubmit={handleRegister}>
                    <fieldset>
                        <legend>Create Account</legend>
                        <label>
                            Username
                            <input
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                minLength={3}
                                maxLength={20}
                            />
                        </label>
                        <label>
                            Password
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                            />
                        </label>
                        <label>
                            Confirm Password
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                        </label>
                        <button type="submit" disabled={registerMutation.isPending} style={{ marginTop: 8 }}>
                            {registerMutation.isPending ? "Creating..." : "Create Account"}
                        </button>
                    </fieldset>
                </form>
            )}
        </div>
    );
};

export default LoginWindow;
