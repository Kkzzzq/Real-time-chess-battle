import { create } from 'zustand'

type Session = { playerId?: string; playerToken?: string; tokenExpiresAt?: number; playerName?: string; seat?: number; matchId?: string }
type Actions = { setSession: (session: Session) => void; clear: () => void; hydrate: () => void }

const KEY = 'rtcb_session'

export const useSessionStore = create<Session & Actions>((set, get) => ({
  setSession: (session) => {
    const merged = { ...get(), ...session }
    localStorage.setItem(KEY, JSON.stringify(merged))
    set(merged)
  },
  clear: () => { localStorage.removeItem(KEY); set({ playerId: undefined, playerToken: undefined, tokenExpiresAt: undefined, playerName: undefined, seat: undefined, matchId: undefined }) },
  hydrate: () => {
    const raw = localStorage.getItem(KEY)
    if (!raw) return
    try {
      const data = JSON.parse(raw) as Session
      if (data.tokenExpiresAt && Date.now() > data.tokenExpiresAt) {
        localStorage.removeItem(KEY)
        return
      }
      set(data)
    } catch { /* ignore */ }
  }
}))
