import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { matchApi } from '../api/matchApi'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'

export function LobbyPage() {
  const [list, setList] = useState<Array<{ match_id: string; status: string }>>([])
  const [name, setName] = useState('Player')
  const [matchId, setMatchId] = useState('')
  const session = useSessionStore()
  const ui = useUiStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (session.matchId) navigate(`/room/${session.matchId}`)
  }, [])

  useEffect(() => {
    matchApi.listMatches().then((m) => setList(m as Array<{ match_id: string; status: string }>)).catch((e) => ui.setError(String(e.message || e)))
  }, [])

  const createAndJoin = async () => {
    try {
      const created = await matchApi.createMatch()
      const joined = await matchApi.joinMatch(created.match_id, name)
      session.setSession({ matchId: created.match_id, playerId: joined.player.player_id, playerToken: joined.player.player_token, seat: joined.player.seat, playerName: joined.player.name })
      navigate(`/room/${created.match_id}`)
    } catch (e: any) {
      ui.setError(e.message)
    }
  }

  const join = async () => {
    try {
      if (!matchId) return
      const joined = await matchApi.joinMatch(matchId, name)
      session.setSession({ matchId, playerId: joined.player.player_id, playerToken: joined.player.player_token, seat: joined.player.seat, playerName: joined.player.name })
      navigate(`/room/${matchId}`)
    } catch (e: any) {
      ui.setError(e.message)
    }
  }

  return <div><h2>大厅</h2>
    <div style={{display:'flex',gap:8,marginBottom:8}}>
      <input value={name} onChange={(e)=>setName(e.target.value)} placeholder='player name' />
      <button onClick={createAndJoin}>创建并加入</button>
    </div>
    <div style={{display:'flex',gap:8,marginBottom:8}}>
      <input value={matchId} onChange={(e)=>setMatchId(e.target.value)} placeholder='match id' />
      <button onClick={join}>加入房间</button>
    </div>
    <ul>{list.map((m)=><li key={m.match_id}>{m.match_id} - {m.status}</li>)}</ul>
  </div>
}
