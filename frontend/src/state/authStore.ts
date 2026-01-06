import { create } from "zustand";
import { persist } from "zustand/middleware";

type AuthUser = {
    id: string;
    username: string;
    playerId: string;
    createdAt: string;
    lastLoginAt: string;
};

type AuthStore = {
    isAuthenticated: boolean;
    token: string | null;
    user: AuthUser | null;
    login: (token: string, user: AuthUser) => void;
    logout: () => void;
};

export const useAuthStore = create<AuthStore>()(
    persist(
        (set) => ({
            isAuthenticated: false,
            token: null,
            user: null,
            login: (token, user) =>
                set({
                    isAuthenticated: true,
                    token,
                    user
                }),
            logout: () =>
                set({
                    isAuthenticated: false,
                    token: null,
                    user: null
                })
        }),
        {
            name: "debate-auth"
        }
    )
);
