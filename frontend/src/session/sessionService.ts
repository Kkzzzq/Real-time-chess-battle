import { useSessionStore } from '../store/sessionStore'

export type ViewerContext = {
  matchId: string
  seat: number
  playerId: string
  playerToken: string
}

export function clearExpiredSession(nowMs: number = Date.now()) {
  const session = useSessionStore.getState().session
  if (!session) return
  if (session.tokenExpiresAt && nowMs > session.tokenExpiresAt) {
    useSessionStore.getState().clearSession()
  }
}

export function getCurrentViewerContext(): ViewerContext | null {
  const session = useSessionStore.getState().session
  if (!session) return null
  return {
    matchId: session.matchId,
    seat: session.seat,
    playerId: session.playerId,
    playerToken: session.playerToken,
  }
}
