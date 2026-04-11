import { useEffect, useState } from 'react'
import { matchApi } from '../api/matchApi'

type Props = { onEnterMatch: (matchId: string) => void }

export function LobbyPage({ onEnterMatch }: Props) {
  const [list, setList] = useState<Array<{ match_id: string; status: string }>>([])
  const [name, setName] = useState('Player')
  const [matchId, setMatchId] = useState('')

  useEffect(() => { matchApi.listMatches().then((m) => setList(m as Array<{ match_id: string; status: string }>)) }, [])

  return <div><h2>大厅</h2>
    <button onClick={async()=>{ const m = await matchApi.createMatch(); onEnterMatch(m.match_id) }}>创建房间</button>
    <div><input value={matchId} onChange={(e)=>setMatchId(e.target.value)} placeholder='match id' />
    <input value={name} onChange={(e)=>setName(e.target.value)} placeholder='player name' />
    <button onClick={()=>onEnterMatch(matchId)}>进入</button></div>
    <ul>{list.map((m)=><li key={m.match_id}>{m.match_id} - {m.status}</li>)}</ul>
  </div>
}
