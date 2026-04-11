import { useEffect } from 'react'
import { matchApi } from '../api/matchApi'
import { useRoomStore } from '../store/roomStore'
import { useSessionStore } from '../store/sessionStore'

type Props = { matchId: string; onStarted: () => void }

export function RoomPage({ matchId, onStarted }: Props) {
  const session = useSessionStore()
  const room = useRoomStore()

  useEffect(() => {
    const run = async () => {
      if (!session.playerId || !session.playerToken) {
        const joined = await matchApi.joinMatch(matchId, session.playerName || 'Player')
        session.setSession({ matchId, playerId: joined.player.player_id, playerToken: joined.player.player_token, seat: joined.player.seat, playerName: joined.player.name })
      }
      const list = await matchApi.listMatches()
      const target = list.find((x)=>x.match_id===matchId)
      if (target) room.setPlayers(target.players as any)
    }
    run()
  }, [matchId])

  return <div><h2>房间 {matchId}</h2>
    <button onClick={async()=>{ if(session.playerId&&session.playerToken) await matchApi.ready(matchId,session.playerId,session.playerToken)}}>Ready</button>
    <button onClick={async()=>{ await matchApi.start(matchId); onStarted() }}>Start</button>
    <ul>{Object.entries(room.players).map(([k,v])=><li key={k}>{v.name} {v.ready?'✅':'⌛'} {v.is_host?'(host)':''}</li>)}</ul>
  </div>
}
