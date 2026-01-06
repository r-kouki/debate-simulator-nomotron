import { create } from "zustand";

export type Notification = {
  id: string;
  type: "info" | "success" | "error" | "achievement";
  title: string;
  message: string;
};

type NotificationState = {
  notifications: Notification[];
  push: (notification: Omit<Notification, "id">) => void;
  remove: (id: string) => void;
};

const makeId = () => Math.random().toString(36).slice(2, 10);

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  push: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          ...notification,
          id: makeId()
        }
      ]
    })),
  remove: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((item) => item.id !== id)
    }))
}));
