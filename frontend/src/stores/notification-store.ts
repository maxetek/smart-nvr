import { create } from "zustand";

export interface Notification {
  id: string;
  event_type: string;
  camera_name: string;
  severity: string;
  timestamp: string;
}

interface NotificationState {
  notifications: Notification[];
  addNotification: (notification: Notification) => void;
  clearNotifications: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],

  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 50),
    })),

  clearNotifications: () => set({ notifications: [] }),
}));
