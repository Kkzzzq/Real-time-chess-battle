import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { matchApi } from '../api/matchApi'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'

type BootstrapReason = 'ok' | 'missing_session' | 'match_not_found' | 'token_expired' | 'player_not_found' | 'auth_failed' | 'unknown'
export type SessionBootstrapResult =
  | { success: true; reason: 'ok'; restored: Awaited<ReturnType<typeof matchApi.reconnect>> }
  | { success: false; reason: Exclude<BootstrapReason, 'ok'> }

function parseReason(err: unknown): Exclude<BootstrapReason, 'ok'> {
  const msg = err instanceof Error ? err.message.toLowerCase() : ''
  if (msg.includes('match not found')) return 'match_not_found'
  if (msg.includes('token expired')) return 'token_expired'
  if (msg.includes('player auth failed') || msg.includes('player not found')) return 'player_not_found'
  if (msg.includes('401') || msg.includes('403')) return 'auth_failed'
  return 'unknown'
}

export function useSessionBootstrap() {
  const session = useSessionStore()
  const ui = useUiStore()
  const navigate = useNavigate()

  return useCallback(async (matchId: string): Promise<SessionBootstrapResult> => {
    if (!session.playerId || !session.playerToken) {
      navigate('/')
      return { success: false, reason: 'missing_session' }
    }
    try {
      const rec = await matchApi.reconnect(matchId, session.playerId, session.playerToken)
      session.setSession({
        matchId,
        seat: rec.player.seat,
        playerId: rec.player.player_id,
        playerName: rec.player.name,
        playerToken: rec.player.player_token,
        tokenExpiresAt: rec.player.player_token_expires_at || undefined
      })
      ui.setError(undefined)
      return { success: true, reason: 'ok', restored: rec }
    } catch (e) {
      const reason = parseReason(e)
      session.clear()
      ui.setError(reason === 'token_expired' ? '会话已过期，请重新加入房间' : '会话恢复失败，请重新加入房间')
      navigate('/')
      return { success: false, reason }
    }
  }, [session.playerId, session.playerToken])
}
