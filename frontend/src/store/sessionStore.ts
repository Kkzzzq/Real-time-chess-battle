import { create } from 'zustand'

type Session = { playerId?: string; playerToken?: string; playerName?: string; seat?: number; matchId?: string }
type Actions = { setSession: (session: Session) => void; clear: () => void; hydrate: () => void }

const KEY = 'rtcb_session'

export const useSessionStore = create<Session & Actions>((set, get) => ({
  setSession: (session) => {
    const merged = { ...get(), ...session }
    localStorage.setItem(KEY, JSON.stringify(merged))
    set(merged)
  },
  clear: () => { localStorage.removeItem(KEY); set({ playerId: undefined, playerToken: undefined, playerName: undefined, seat: undefined, matchId: undefined }) },
  hydrate: () => {
    const raw = localStorage.getItem(KEY)
    if (!raw) return
    try { set(JSON.parse(raw)) } catch { /* ignore */ }
  }
}))
