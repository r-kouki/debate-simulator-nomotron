import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark";

type ThemeStore = {
    theme: Theme;
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
};

// Apply theme to DOM
const applyTheme = (theme: Theme) => {
    document.documentElement.setAttribute("data-theme", theme);
};

export const useThemeStore = create<ThemeStore>()(
    persist(
        (set, get) => ({
            theme: "light",
            setTheme: (theme) => {
                applyTheme(theme);
                set({ theme });
            },
            toggleTheme: () => {
                const newTheme = get().theme === "light" ? "dark" : "light";
                applyTheme(newTheme);
                set({ theme: newTheme });
            }
        }),
        {
            name: "debate-theme"
        }
    )
);

// Initialize theme on first load (called from App.tsx)
export const initializeTheme = () => {
    const storedTheme = localStorage.getItem("debate-theme");
    if (storedTheme) {
        try {
            const parsed = JSON.parse(storedTheme);
            if (parsed.state?.theme) {
                applyTheme(parsed.state.theme);
            }
        } catch {
            // Fallback to light theme
            applyTheme("light");
        }
    }
};
