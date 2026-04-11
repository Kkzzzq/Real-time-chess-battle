import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { matchApi } from '../api/matchApi'
import { queryApi } from '../api/queryApi'
import { useRoomStore } from '../store/roomStore'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'
import { useMatchStore } from '../store/matchStore'
import { useSessionBootstrap } from '../hooks/useSessionBootstrap'
import { useMatchRealtime } from '../hooks/useMatchRealtime'
import { StatusBanner } from '../components/layout/StatusBanner'
import { useWsStore } from '../store/wsStore'

export function RoomPage() {
  const { matchId = '' } = useParams()
  const navigate = useNavigate()
  const session = useSessionStore()
  const room = useRoomStore()
  const ui = useUiStore()
  const ws = useWsStore()
  const { snapshot } = useMatchStore()

  const bootstrap = useSessionBootstrap()

  useMatchRealtime(matchId, session.playerId, session.playerToken)

  const loadRoom = async () => {
    room.setLoading(true)
    room.setMatchId(matchId)
    try {
      const rec = await bootstrap(matchId)
      if (!rec) return
      const st = await queryApi.state(matchId, session.playerId, session.playerToken)
      room.setPlayers(st.players as any)
      room.setStatus(st.match_meta.status)
      ui.setError(undefined)
      if (st.match_meta.status === 'running') navigate(`/game/${matchId}`)
    } finally {
      room.setLoading(false)
    }
  }

  useEffect(() => { loadRoom() }, [matchId])

  useEffect(() => {
    if (!snapshot) return
    room.setPlayers(snapshot.players as any)
    room.setStatus(snapshot.match_meta.status)
    if (snapshot.match_meta.status === 'running') navigate(`/game/${matchId}`)
  }, [snapshot?.match_meta.version])

  const me = Object.values(room.players).find((p) => p.player_id === session.playerId)
  const isHost = !!me?.is_host

  return <div><h2>房间 {matchId}</h2>
    <StatusBanner loading={room.loading} error={ui.error || room.roomError} notice={ws.reconnecting ? '连接重试中...' : undefined} onRetry={loadRoom} />
    <div>我是: seat {session.seat ?? '-'} {isHost ? '(Host)' : ''}</div>
    <button onClick={async()=>{ if(session.playerId&&session.playerToken){ await matchApi.ready(matchId,session.playerId,session.playerToken) }}}>Ready</button>
    <button disabled={!isHost} onClick={async()=>{ if(session.playerId&&session.playerToken){ const started = await matchApi.start(matchId, session.playerId, session.playerToken); if(started.status==='running') navigate(`/game/${matchId}`) } }}>Start</button>
    <button onClick={async()=>{ if(session.playerId&&session.playerToken){ await matchApi.leave(matchId,session.playerId,session.playerToken); session.clear(); navigate('/') }}}>Leave</button>
    <ul>{Object.entries(room.players).map(([k,v])=><li key={k}>{v.name} {v.ready?'✅':'⌛'} {v.is_host?'(host)':''} {v.online?'':'(offline)'}</li>)}</ul>
  </div>
}
