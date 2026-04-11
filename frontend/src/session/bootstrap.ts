import { clearExpiredSession, getCurrentViewerContext } from './sessionService'

export type BootstrapResult =
  | { ok: true; target: 'lobby' | 'room' | 'game'; matchId?: string }
  | { ok: false; reason: 'missing_session' | 'expired_session' }

export function bootstrapSession(pathname: string): BootstrapResult {
  const before = getCurrentViewerContext()
  clearExpiredSession()
  const after = getCurrentViewerContext()

  if (before && !after) {
    return { ok: false, reason: 'expired_session' }
  }
  if (!after) {
    return { ok: false, reason: 'missing_session' }
  }

  if (pathname.startsWith('/game/')) return { ok: true, target: 'game', matchId: after.matchId }
  if (pathname.startsWith('/room/')) return { ok: true, target: 'room', matchId: after.matchId }
  return { ok: true, target: 'lobby' }
}
