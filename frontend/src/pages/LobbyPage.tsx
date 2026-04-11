import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { matchApi } from '../api/matchApi'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'
import { StatusBanner } from '../components/layout/StatusBanner'

export function LobbyPage() {
  const [list, setList] = useState<Array<{ match_id: string; status: string }>>([])
  const [name, setName] = useState('Player')
  const [matchId, setMatchId] = useState('')
  const [loading, setLoading] = useState(false)
  const session = useSessionStore()
  const ui = useUiStore()
  const navigate = useNavigate()

  const refresh = async () => {
    setLoading(true)
    try {
      const m = await matchApi.listMatches()
      setList(m as Array<{ match_id: string; status: string }>)
      ui.setError(undefined)
    } catch (e: any) {
      ui.setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (session.matchId) navigate(`/room/${session.matchId}`)
    refresh()
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
    <StatusBanner loading={loading} error={ui.error} onRetry={refresh} />
    <div style={{display:'flex',gap:8,marginBottom:8}}>
      <input value={name} onChange={(e)=>setName(e.target.value)} placeholder='player name' />
      <button onClick={createAndJoin}>创建并加入</button>
    </div>
    <div style={{display:'flex',gap:8,marginBottom:8}}>
      <input value={matchId} onChange={(e)=>setMatchId(e.target.value)} placeholder='match id' />
      <button onClick={join}>加入房间</button>
      <button onClick={refresh}>刷新列表</button>
    </div>
    {list.length === 0 ? <div>暂无可用房间</div> : <ul>{list.map((m)=><li key={m.match_id}>{m.match_id} - {m.status}</li>)}</ul>}
  </div>
}
