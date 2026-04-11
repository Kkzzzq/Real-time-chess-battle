import { create } from 'zustand'
import type { EventSchema, MatchSnapshot } from '../types/contracts'

interface MatchState {
  snapshot?: MatchSnapshot
  recentEvents: EventSchema[]
  commandResult?: { ok: boolean; message: string }
  subscribedMeta?: Record<string, unknown>
  setSnapshot: (snapshot: MatchSnapshot) => void
  pushEvents: (events: EventSchema[]) => void
  setCommandResult: (result: { ok: boolean; message: string }) => void
  setSubscribedMeta: (meta: Record<string, unknown>) => void
}

export const useMatchStore = create<MatchState>((set, get) => ({
  snapshot: undefined,
  recentEvents: [],
  setSnapshot: (snapshot) => set({ snapshot, recentEvents: snapshot.events }),
  pushEvents: (events) => set({ recentEvents: [...get().recentEvents, ...events].slice(-80) }),
  setCommandResult: (commandResult) => set({ commandResult }),
  setSubscribedMeta: (subscribedMeta) => set({ subscribedMeta })
}))
