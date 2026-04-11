import { useEffect } from 'react'
import { queryApi } from '../api/queryApi'
import { commandApi } from '../api/commandApi'
import { useMatchStore } from '../store/matchStore'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'
import { Board } from '../components/board/Board'
import { ConnectionStatus } from '../components/layout/ConnectionStatus'
import { useMatchRealtime } from '../hooks/useMatchRealtime'

export function GamePage() {
  const { snapshot, setSnapshot } = useMatchStore()
  const session = useSessionStore()
  const ui = useUiStore()

  useMatchRealtime(session.matchId, session.playerId, session.playerToken)

  useEffect(() => {
    if (!session.matchId) return
    queryApi.state(session.matchId, session.playerId, session.playerToken).then(setSnapshot)
  }, [session.matchId, session.playerId, session.playerToken])

  const onPieceClick = async (pieceId: string) => {
    if (!session.matchId) return
    const legal = await queryApi.legalMoves(session.matchId, pieceId, session.playerId, session.playerToken)
    ui.setSelection(pieceId, legal.actionable?.actionable_targets || [])
  }
  const onCellClick = async (x:number,y:number) => {
    if (!session.matchId || !session.playerId || !session.playerToken || !ui.selectedPieceId) return
    await commandApi.move(session.matchId, { player_id: session.playerId, player_token: session.playerToken, piece_id: ui.selectedPieceId, target_x: x, target_y: y })
    ui.setSelection(undefined, [])
  }

  return <div><h2>对局</h2><ConnectionStatus />
    <div>Phase: {snapshot?.phase.name} / Winner: {snapshot?.match_meta.winner ?? '-'}</div>
    <button onClick={async()=>{ if(session.matchId&&session.playerId&&session.playerToken){ if(confirm('确认认输?')) await commandApi.resign(session.matchId,{player_id:session.playerId,player_token:session.playerToken})}}}>Resign</button>
    <Board snapshot={snapshot} selectedPieceId={ui.selectedPieceId} actionableTargets={ui.actionableTargets} onCellClick={onCellClick} onPieceClick={onPieceClick} />
  </div>
}
