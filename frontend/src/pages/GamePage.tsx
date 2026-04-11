import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { queryApi } from '../api/queryApi'
import { commandApi } from '../api/commandApi'
import { matchApi } from '../api/matchApi'
import { useMatchStore } from '../store/matchStore'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'
import { Board } from '../components/board/Board'
import { ConnectionStatus } from '../components/layout/ConnectionStatus'
import { useMatchRealtime } from '../hooks/useMatchRealtime'

export function GamePage() {
  const { matchId = '' } = useParams()
  const navigate = useNavigate()
  const { snapshot, setSnapshot, recentEvents, commandResult } = useMatchStore()
  const session = useSessionStore()
  const ui = useUiStore()

  useMatchRealtime(matchId, session.playerId, session.playerToken)

  useEffect(() => {
    let timer: number | undefined
    const run = async () => {
      if (!session.playerId || !session.playerToken) { navigate('/'); return }
      try {
        await matchApi.reconnect(matchId, session.playerId, session.playerToken)
        const tick = async () => {
          const st = await queryApi.state(matchId, session.playerId, session.playerToken)
          setSnapshot(st)
          if (st.match_meta.status === 'ended') ui.setNotice('对局已结束')
        }
        await tick()
        timer = window.setInterval(tick, 1500)
      } catch {
        session.clear(); navigate('/')
      }
    }
    run()
    return () => { if (timer) clearInterval(timer) }
  }, [matchId, session.playerId, session.playerToken])

  const onPieceClick = async (pieceId: string) => {
    if (!session.playerId || !session.playerToken) return
    const piece = snapshot?.pieces.find((p) => p.id === pieceId)
    if (!piece || piece.commandability.viewer_can_command === false) {
      ui.setError(piece?.commandability.viewer_disabled_reason || '当前棋子不可操作')
      return
    }
    const legal = await queryApi.legalMoves(matchId, pieceId, session.playerId, session.playerToken)
    ui.setSelection(pieceId, legal.actionable?.actionable_targets || [])
  }
  const onCellClick = async (x:number,y:number) => {
    if (!session.playerId || !session.playerToken || !ui.selectedPieceId) return
    try {
      await commandApi.move(matchId, { player_id: session.playerId, player_token: session.playerToken, piece_id: ui.selectedPieceId, target_x: x, target_y: y })
      ui.setSelection(undefined, [])
    } catch (e:any) {
      ui.setError(e.message)
    }
  }

  const unlockPlayer = snapshot?.unlock.players?.[String(session.seat || '')]

  return <div><h2>对局 {matchId}</h2><ConnectionStatus />
    <div>Phase: {snapshot?.phase.name} ({snapshot?.phase.remaining_ms ?? '-'}ms) wave={snapshot?.unlock.current_wave}</div>
    <div>Next: {snapshot?.phase.next_phase_name ?? '-'} / Winner: {snapshot?.match_meta.winner ?? '-'} / Reason: {snapshot?.match_meta.reason ?? '-'}</div>
    {snapshot?.match_meta.status === 'ended' && <div style={{padding:8,background:'#fff1f0',margin:'8px 0'}}>结算：winner={snapshot?.match_meta.winner ?? 'draw'} reason={snapshot?.match_meta.reason ?? 'unknown'} <button onClick={()=>navigate('/')}>返回大厅</button> <button onClick={()=>navigate(`/room/${matchId}`)}>返回房间</button></div>}

    <div style={{margin:'8px 0',padding:8,border:'1px solid #ddd'}}>
      <strong>Unlock</strong> window={String(snapshot?.unlock.window_open)} remaining={snapshot?.unlock.current_wave_remaining_ms ?? '-'}
      <div>可选：{unlockPlayer?.available_options?.join(', ') || '-'}</div>
      <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
        {(unlockPlayer?.available_options || []).map((k) => <button key={k} onClick={async()=>{ if(session.playerId&&session.playerToken){ await commandApi.unlock(matchId,{player_id:session.playerId,player_token:session.playerToken,kind:k}) } }}>{k}</button>)}
      </div>
    </div>

    <button onClick={async()=>{ if(session.playerId&&session.playerToken){ if(confirm('确认认输?')) await commandApi.resign(matchId,{player_id:session.playerId,player_token:session.playerToken})}}}>Resign</button>
    <Board snapshot={snapshot} selectedPieceId={ui.selectedPieceId} actionableTargets={ui.actionableTargets} onCellClick={onCellClick} onPieceClick={onPieceClick} />

    <div style={{marginTop:8}}>Command Result: {commandResult ? `${String(commandResult.ok)} ${commandResult.message}` : '-'}</div>
    <div>错误: {ui.error || '-'}</div>
    <div style={{maxHeight:180,overflow:'auto',border:'1px solid #eee',padding:6,marginTop:8}}>
      <strong>Events</strong>
      <ul>{recentEvents.slice(-20).map((e,idx)=><li key={idx}>{e.type} @ {e.ts_ms}</li>)}</ul>
    </div>

    <div style={{marginTop:8,border:'1px solid #eee',padding:6}}>
      <strong>Pieces Status</strong>
      <ul>{(snapshot?.pieces || []).filter(p=>p.alive).slice(0,12).map((p)=><li key={p.id}>{p.id} cd={p.cooldown_remaining_ms} move={p.move_remaining_ms} can={String(p.commandability.viewer_can_command)} reason={p.commandability.viewer_disabled_reason || '-'}</li>)}</ul>
    </div>
  </div>
}
