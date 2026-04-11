import { create } from 'zustand'
import type { EventSchema, MatchSnapshot } from '../types/contracts'

const eventKey = (e: EventSchema) => `${e.type}:${e.ts_ms}:${JSON.stringify(e.payload)}`

function mergeEvents(prev: EventSchema[], incoming: EventSchema[]): EventSchema[] {
  const map = new Map<string, EventSchema>()
  for (const e of [...prev, ...incoming]) map.set(eventKey(e), e)
  return Array.from(map.values()).sort((a, b) => a.ts_ms - b.ts_ms).slice(-120)
}

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
  setSnapshot: (snapshot) => set({ snapshot, recentEvents: mergeEvents(get().recentEvents, snapshot.events || []) }),
  pushEvents: (events) => set({ recentEvents: mergeEvents(get().recentEvents, events) }),
  setCommandResult: (commandResult) => set({ commandResult }),
  setSubscribedMeta: (subscribedMeta) => set({ subscribedMeta })
}))
