import { useEffect, useState } from 'react'
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
import { UnlockPanel } from '../components/layout/UnlockPanel'
import { StatusBanner } from '../components/layout/StatusBanner'

export function GamePage() {
  const { matchId = '' } = useParams()
  const navigate = useNavigate()
  const { snapshot, setSnapshot, recentEvents, commandResult } = useMatchStore()
  const session = useSessionStore()
  const ui = useUiStore()
  const [loading, setLoading] = useState(true)
  const [unlockLoading, setUnlockLoading] = useState(false)

  useMatchRealtime(matchId, session.playerId, session.playerToken)

  const loadInitial = async () => {
    if (!session.playerId || !session.playerToken) { navigate('/'); return }
    setLoading(true)
    try {
      await matchApi.reconnect(matchId, session.playerId, session.playerToken)
      const st = await queryApi.state(matchId, session.playerId, session.playerToken)
      setSnapshot(st)
      ui.setError(undefined)
    } catch {
      session.clear()
      ui.setError('reconnect 失败，请重新加入房间')
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadInitial() }, [matchId, session.playerId, session.playerToken])

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
  const onCellClick = async (x: number, y: number) => {
    if (!session.playerId || !session.playerToken || !ui.selectedPieceId) return
    try {
      await commandApi.move(matchId, {
        player_id: session.playerId,
        player_token: session.playerToken,
        piece_id: ui.selectedPieceId,
        target_x: x,
        target_y: y,
      })
      ui.setSelection(undefined, [])
      ui.setError(undefined)
    } catch (e: any) {
      ui.setError(e.message)
    }
  }

  return (
    <div>
      <h2>对局 {matchId}</h2>
      <ConnectionStatus />
      <StatusBanner loading={loading} error={ui.error} notice={ui.notice} onRetry={loadInitial} />

      <div>
        Phase: {snapshot?.phase.name} ({snapshot?.phase.remaining_ms ?? '-'}ms) wave={snapshot?.unlock.current_wave} next={snapshot?.phase.next_phase_name ?? '-'}
      </div>

      {snapshot?.match_meta.status === 'ended' && (
        <div style={{ padding: 8, background: '#fff1f0', margin: '8px 0' }}>
          结算：winner={snapshot?.match_meta.winner ?? 'draw'} reason={snapshot?.match_meta.reason ?? 'unknown'}
          <button onClick={() => navigate('/')}>返回大厅</button>
          <button onClick={() => navigate(`/room/${matchId}`)}>返回房间</button>
        </div>
      )}

      <UnlockPanel
        unlock={snapshot?.unlock}
        seat={session.seat}
        loading={unlockLoading}
        onChoose={async (k) => {
          if (!session.playerId || !session.playerToken) return
          setUnlockLoading(true)
          try {
            await commandApi.unlock(matchId, { player_id: session.playerId, player_token: session.playerToken, kind: k })
          } catch (e: any) {
            ui.setError(e.message)
          } finally {
            setUnlockLoading(false)
          }
        }}
      />

      <button onClick={async () => { if (session.playerId && session.playerToken && confirm('确认认输?')) await commandApi.resign(matchId, { player_id: session.playerId, player_token: session.playerToken }) }}>Resign</button>
      <Board snapshot={snapshot} selectedPieceId={ui.selectedPieceId} actionableTargets={ui.actionableTargets} onCellClick={onCellClick} onPieceClick={onPieceClick} />

      <div style={{ marginTop: 8 }}>Command Result: {commandResult ? `${String(commandResult.ok)} ${commandResult.message}` : '-'}</div>
      <div style={{ maxHeight: 180, overflow: 'auto', border: '1px solid #eee', padding: 6, marginTop: 8 }}>
        <strong>Events</strong>
        <ul>{recentEvents.slice(-20).map((e, idx) => <li key={idx}>{e.type} @ {e.ts_ms}</li>)}</ul>
      </div>
    </div>
  )
}
