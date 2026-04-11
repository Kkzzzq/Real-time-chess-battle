import { useSessionStore } from '../store/sessionStore'

export type ViewerContext = {
  matchId: string
  seat: number
  playerId: string
  playerToken: string
}

export function clearExpiredSession(nowMs: number = Date.now()) {
  const state = useSessionStore.getState()
  if (state.tokenExpiresAt && nowMs > state.tokenExpiresAt) {
    state.clear()
  }
}

export function getCurrentViewerContext(): ViewerContext | null {
  const state = useSessionStore.getState()
  if (!state.matchId || !state.playerId || !state.playerToken || !state.seat) return null
  return {
    matchId: state.matchId,
    seat: state.seat,
    playerId: state.playerId,
    playerToken: state.playerToken,
  }
}
