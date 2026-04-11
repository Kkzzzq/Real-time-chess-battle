import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { queryApi } from '../api/queryApi'
import { useMatchStore } from '../store/matchStore'
import { useRoomStore } from '../store/roomStore'
import { useUiStore } from '../store/uiStore'
import { useSessionBootstrap } from './useSessionBootstrap'

export function useRoomController(matchId: string) {
  const navigate = useNavigate()
  const room = useRoomStore()
  const ui = useUiStore()
  const { snapshot } = useMatchStore()
  const bootstrap = useSessionBootstrap()

  const loadRoom = useCallback(async () => {
    room.setLoading(true)
    room.setReconnecting(true)
    room.setMatchId(matchId)
    room.setDenied(false)
    room.setDeleted(false)
    try {
      const rec = await bootstrap(matchId)
      if (!rec.success) {
        room.setDenied(true)
        return
      }
      const st = await queryApi.state(matchId, rec.restored.player.player_id, rec.restored.player.player_token)
      room.setPlayers(st.players as any)
      room.setStatus(st.match_meta.status)
      if (st.match_meta.status === 'deleted') room.setDeleted(true)
      ui.setError(undefined)
      if (st.match_meta.status === 'running') navigate(`/game/${matchId}`)
    } finally {
      room.setLoading(false)
      room.setReconnecting(false)
    }
  }, [bootstrap, matchId, navigate, room, ui])

  const syncFromSnapshot = useCallback(() => {
    if (!snapshot) return
    room.setPlayers(snapshot.players as any)
    room.setStatus(snapshot.match_meta.status)
    if (snapshot.match_meta.status === 'running') navigate(`/game/${matchId}`)
  }, [matchId, navigate, room, snapshot])

  return { loadRoom, syncFromSnapshot }
}
