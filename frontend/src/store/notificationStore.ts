import { create } from 'zustand'

export type NotificationLevel = 'info' | 'success' | 'warning' | 'error'

export type NotificationItem = {
  id: string
  message: string
  level: NotificationLevel
  ts: number
}

type NotificationState = {
  items: NotificationItem[]
  push: (message: string, level?: NotificationLevel) => void
  remove: (id: string) => void
  clear: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  items: [],
  push: (message, level = 'info') =>
    set((s) => ({
      items: [...s.items, { id: Math.random().toString(36).slice(2), message, level, ts: Date.now() }],
    })),
  remove: (id) => set((s) => ({ items: s.items.filter((v) => v.id !== id) })),
  clear: () => set({ items: [] }),
}))
