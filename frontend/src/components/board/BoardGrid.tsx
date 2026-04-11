import type { MatchSnapshot } from '../../types/contracts'

type Props = {
  snapshot?: MatchSnapshot
  actionableTargets: [number, number][]
  selectedPieceId?: string
  onCellClick: (x: number, y: number) => void
  onPieceClick: (pieceId: string) => void
}

export function BoardGrid({ snapshot, actionableTargets, selectedPieceId, onCellClick, onPieceClick }: Props) {
  const runtimeCells = snapshot?.runtime_board.cells
  const isTarget = (x: number, y: number) => actionableTargets.some(([tx, ty]) => tx === x && ty === y)

  const handleCell = (x: number, y: number, primaryId?: string) => {
    if (selectedPieceId) return onCellClick(x, y)
    if (primaryId) return onPieceClick(primaryId)
    return onCellClick(x, y)
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(9,56px)', gap: 0, position: 'absolute', inset: 0 }}>
      {Array.from({ length: 10 }).flatMap((_, y) =>
        Array.from({ length: 9 }).map((__, x) => {
          const cell = runtimeCells?.[y]?.[x]
          const primary = cell?.primary_occupant
          const multi = (cell?.occupants.length || 0) > 1
          return (
            <button
              key={`${x}-${y}`}
              onClick={() => handleCell(x, y, primary?.piece_id)}
              style={{
                height: 56,
                width: 56,
                background: isTarget(x, y) ? '#ffe58f' : multi ? '#fff1f0' : '#f5f5f5',
                border: '1px solid #d9d9d9',
                fontSize: 11,
              }}
              title={multi ? `occupants=${cell?.occupants.length}` : ''}
            >
              {primary ? `${primary.owner === 1 ? '红' : '黑'}${primary.kind}` : ''}
              {multi ? <div style={{ fontSize: 10, color: '#cf1322' }}>+{(cell?.occupants.length || 1) - 1}</div> : null}
            </button>
          )
        })
      )}
    </div>
  )
}
