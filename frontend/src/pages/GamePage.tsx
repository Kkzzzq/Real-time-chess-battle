import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMatchStore } from '../store/matchStore'
import { useSessionStore } from '../store/sessionStore'
import { useUiStore } from '../store/uiStore'
import { Board } from '../components/board/Board'
import { ConnectionStatus } from '../components/layout/ConnectionStatus'
import { useMatchRealtime } from '../hooks/useMatchRealtime'
import { UnlockPanel } from '../components/layout/UnlockPanel'
import { StatusBanner } from '../components/layout/StatusBanner'
import { PhasePanel } from '../components/layout/PhasePanel'
import { EventsPanel } from '../components/layout/EventsPanel'
import { ResultPanel } from '../components/layout/ResultPanel'
import { PieceStatusPanel } from '../components/layout/PieceStatusPanel'
import { useGameController } from '../hooks/useGameController'

export function GamePage() {
  const { matchId = '' } = useParams()
  const { snapshot, recentEvents, commandResult } = useMatchStore()
  const session = useSessionStore()
  const ui = useUiStore()
  const [loading, setLoading] = useState(true)
  const [unlockLoading, setUnlockLoading] = useState(false)
  const controller = useGameController(matchId, session.playerId, session.playerToken)

  useMatchRealtime(matchId, session.playerId, session.playerToken)

  const loadInitial = async () => {
    setLoading(true)
    try {
      await controller.loadInitial()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadInitial() }, [matchId, session.playerId, session.playerToken])

  const ended = controller.ended

  return (
    <div>
      <h2>对局 {matchId}</h2>
      <ConnectionStatus />
      <StatusBanner loading={loading} error={ui.error} notice={ui.notice} onRetry={loadInitial} />

      <PhasePanel snapshot={snapshot} />
      <ResultPanel snapshot={snapshot} matchId={matchId} />

      <UnlockPanel
        unlock={snapshot?.unlock}
        seat={session.seat}
        loading={unlockLoading || ended}
        onChoose={async (k) => {
          setUnlockLoading(true)
          try {
            await controller.unlock(k)
          } catch (e: any) {
            ui.setError(e.message)
          } finally {
            setUnlockLoading(false)
          }
        }}
      />

      <button disabled={ended} onClick={async () => { if (confirm('确认认输?')) await controller.resign() }}>Resign</button>
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <Board
          snapshot={snapshot}
          selectedPieceId={ui.selectedPieceId}
          actionableTargets={ui.actionableTargets}
          showRuntimeDebug={false}
          onCellClick={async (x, y) => { if (!ended) await controller.moveTo(x, y) }}
          onPieceClick={async (pieceId) => {
            if (ended) return
            const piece = snapshot?.pieces.find((p) => p.id === pieceId)
            if (!piece || piece.commandability.viewer_can_command === false) {
              ui.setError(piece?.commandability.viewer_disabled_reason || '当前棋子不可操作')
              return
            }
            await controller.selectPiece(pieceId)
          }}
        />
        {ended ? <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.18)', pointerEvents: 'all' }} /> : null}
      </div>

      <div style={{ marginTop: 8 }}>Command Result: {commandResult ? `${String(commandResult.ok)} ${commandResult.message}` : '-'}</div>
      <EventsPanel events={recentEvents} />
      <PieceStatusPanel pieces={snapshot?.pieces || []} />
    </div>
  )
}
