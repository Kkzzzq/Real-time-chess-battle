import { useSessionStore } from '../store/sessionStore'

export type ViewerContext = {
  matchId: string
  seat: number
  playerId: string
  playerToken: string
}

export function clearExpiredSession(nowMs: number = Date.now()) {
<<<<<<< HEAD
  const state = useSessionStore.getState()
  if (state.tokenExpiresAt && nowMs > state.tokenExpiresAt) {
    state.clear()
=======
  const session = useSessionStore.getState().session
  if (!session) return
  if (session.tokenExpiresAt && nowMs > session.tokenExpiresAt) {
    useSessionStore.getState().clearSession()
>>>>>>> origin/main
  }
}

export function getCurrentViewerContext(): ViewerContext | null {
<<<<<<< HEAD
  const state = useSessionStore.getState()
  if (!state.matchId || !state.playerId || !state.playerToken || !state.seat) return null
  return {
    matchId: state.matchId,
    seat: state.seat,
    playerId: state.playerId,
    playerToken: state.playerToken,
=======
  const session = useSessionStore.getState().session
  if (!session) return null
  return {
    matchId: session.matchId,
    seat: session.seat,
    playerId: session.playerId,
    playerToken: session.playerToken,
>>>>>>> origin/main
  }
}
