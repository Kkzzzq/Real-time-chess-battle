import { useNavigate } from 'react-router-dom'
import type { MatchSnapshot } from '../../types/contracts'

export function ResultPanel({ snapshot, matchId }: { snapshot?: MatchSnapshot; matchId: string }) {
  const navigate = useNavigate()
  if (snapshot?.match_meta.status !== 'ended') return null
  return <div style={{ padding: 8, background: '#fff1f0', margin: '8px 0' }}>
    <strong>对局结束</strong> winner={snapshot.match_meta.winner ?? 'draw'} reason={snapshot.match_meta.reason ?? 'unknown'}
    <button onClick={() => navigate('/')}>返回大厅</button>
    <button onClick={() => navigate(`/room/${matchId}`)}>返回房间</button>
  </div>
}
