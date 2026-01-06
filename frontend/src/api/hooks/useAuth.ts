import { useMutation } from "@tanstack/react-query";
import { useSettingsStore } from "../../state/settingsStore";
import { useAuthStore } from "../../state/authStore";

type AuthUser = {
    id: string;
    username: string;
    playerId: string;
    createdAt: string;
    lastLoginAt: string;
};

type AuthResponse =
    | { success: true; token: string; user: AuthUser }
    | { success: false; error: string };

const getBaseUrl = (override?: string) => {
    if (override) return override;
    return import.meta.env.VITE_API_URL || "http://localhost:3001";
};

export const useLogin = () => {
    const { apiBaseUrlOverride } = useSettingsStore();
    const { login } = useAuthStore();

    return useMutation({
        mutationFn: async ({ username, password }: { username: string; password: string }) => {
            const response = await fetch(`${getBaseUrl(apiBaseUrlOverride)}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data: AuthResponse = await response.json();
            if (!data.success) {
                throw new Error(data.error);
            }
            return data;
        },
        onSuccess: (data) => {
            if (data.success) {
                login(data.token, data.user);
            }
        }
    });
};

export const useRegister = () => {
    const { apiBaseUrlOverride } = useSettingsStore();
    const { login } = useAuthStore();

    return useMutation({
        mutationFn: async ({ username, password }: { username: string; password: string }) => {
            const response = await fetch(`${getBaseUrl(apiBaseUrlOverride)}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data: AuthResponse = await response.json();
            if (!data.success) {
                throw new Error(data.error);
            }
            return data;
        },
        onSuccess: (data) => {
            if (data.success) {
                login(data.token, data.user);
            }
        }
    });
};
