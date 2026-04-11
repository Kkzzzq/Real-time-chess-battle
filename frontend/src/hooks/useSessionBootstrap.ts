import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { matchApi } from '../api/matchApi'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'

export function useSessionBootstrap() {
  const session = useSessionStore()
  const ui = useUiStore()
  const navigate = useNavigate()

  return useCallback(async (matchId: string) => {
    if (!session.playerId || !session.playerToken) {
      navigate('/')
      return null
    }
    try {
      const rec = await matchApi.reconnect(matchId, session.playerId, session.playerToken)
      session.setSession({ matchId, seat: rec.player.seat, tokenExpiresAt: rec.player.player_token_expires_at || undefined })
      ui.setError(undefined)
      return rec
    } catch {
      session.clear()
      ui.setError('会话恢复失败，请重新加入房间')
      navigate('/')
      return null
    }
  }, [session.playerId, session.playerToken])
}
