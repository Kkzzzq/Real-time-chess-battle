import type { MatchSnapshot } from '../../types/contracts'
import { BoardCellOverlay } from './BoardCellOverlay'
import { BoardDebugOverlay } from './BoardDebugOverlay'
import { BoardGrid } from './BoardGrid'
import { PieceLayer } from './PieceLayer'

type Props = {
  snapshot?: MatchSnapshot
  selectedPieceId?: string
  actionableTargets: [number, number][]
  onCellClick: (x: number, y: number) => void
  onPieceClick: (pieceId: string) => void
  showRuntimeDebug?: boolean
}

export function Board({ snapshot, selectedPieceId, actionableTargets, onCellClick, onPieceClick, showRuntimeDebug = false }: Props) {
  return (
    <div style={{ position: 'relative', width: 9 * 56, height: 10 * 56 }}>
      <BoardGrid
        snapshot={snapshot}
        actionableTargets={actionableTargets}
        selectedPieceId={selectedPieceId}
        onCellClick={onCellClick}
        onPieceClick={onPieceClick}
      />
      <BoardCellOverlay snapshot={snapshot} />
      <PieceLayer snapshot={snapshot} selectedPieceId={selectedPieceId} />
      <BoardDebugOverlay snapshot={snapshot} enabled={showRuntimeDebug} />
    </div>
  )
}
