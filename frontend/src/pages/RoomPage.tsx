import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { matchApi } from '../api/matchApi'
import { queryApi } from '../api/queryApi'
import { useRoomStore } from '../store/roomStore'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'

export function RoomPage() {
  const { matchId = '' } = useParams()
  const navigate = useNavigate()
  const session = useSessionStore()
  const room = useRoomStore()
  const ui = useUiStore()

  useEffect(() => {
    let timer: number | undefined
    const boot = async () => {
      try {
        if (!session.playerId || !session.playerToken) {
          navigate('/')
          return
        }
        await matchApi.reconnect(matchId, session.playerId, session.playerToken)
        session.setSession({ matchId })

        const tick = async () => {
          try {
            const st = await queryApi.state(matchId, session.playerId, session.playerToken)
            room.setPlayers(st.players as any)
            room.setStatus(st.match_meta.status)
            if (st.match_meta.status === 'running') navigate(`/game/${matchId}`)
          } catch (e: any) {
            ui.setError(e.message)
          }
        }
        await tick()
        timer = window.setInterval(tick, 2000)
      } catch {
        session.clear()
        navigate('/')
      }
    }
    boot()
    return () => { if (timer) clearInterval(timer) }
  }, [matchId])

  const me = Object.values(room.players).find((p) => p.player_id === session.playerId)
  const isHost = !!me?.is_host

  return <div><h2>房间 {matchId}</h2>
    <div>我是: seat {session.seat ?? '-'} {isHost ? '(Host)' : ''}</div>
    <button onClick={async()=>{ if(session.playerId&&session.playerToken){ await matchApi.ready(matchId,session.playerId,session.playerToken) }}}>Ready</button>
    <button disabled={!isHost} onClick={async()=>{ const started:any = await matchApi.start(matchId); if(started.status==='running') navigate(`/game/${matchId}`) }}>Start</button>
    <button onClick={async()=>{ if(session.playerId&&session.playerToken){ await matchApi.leave(matchId,session.playerId,session.playerToken); session.clear(); navigate('/') }}}>Leave</button>
    <ul>{Object.entries(room.players).map(([k,v])=><li key={k}>{v.name} {v.ready?'✅':'⌛'} {v.is_host?'(host)':''} {v.online?'':'(offline)'}</li>)}</ul>
  </div>
}
