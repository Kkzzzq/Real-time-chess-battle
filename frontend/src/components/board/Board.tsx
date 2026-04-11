import type { MatchSnapshot } from '../../types/contracts'

type Props = {
  snapshot?: MatchSnapshot
  selectedPieceId?: string
  actionableTargets: [number, number][]
  onCellClick: (x: number, y: number) => void
  onPieceClick: (pieceId: string) => void
}

export function Board({ snapshot, selectedPieceId, actionableTargets, onCellClick, onPieceClick }: Props) {
  const runtimeCells = snapshot?.runtime_board.cells
  const pieces = snapshot?.pieces.filter((p) => p.alive) || []
  const isTarget = (x: number, y: number) => actionableTargets.some(([tx, ty]) => tx === x && ty === y)

  return (
    <div style={{ position: 'relative', width: 9 * 56, height: 10 * 56 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(9,56px)', gap: 0, position: 'absolute', inset: 0 }}>
        {Array.from({ length: 10 }).flatMap((_, y) =>
          Array.from({ length: 9 }).map((__, x) => {
            const cell = runtimeCells?.[y]?.[x]
            const primary = cell?.primary_occupant
            const multi = (cell?.occupants.length || 0) > 1
            return (
              <button
                key={`${x}-${y}`}
                onClick={() => (primary ? onPieceClick(primary.piece_id) : onCellClick(x, y))}
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
              </button>
            )
          })
        )}
      </div>

      {/* display_x/display_y overlay layer for smooth movement */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {pieces.map((p) => {
          const can = p.commandability.viewer_can_command
          return (
            <div
              key={p.id}
              style={{
                position: 'absolute',
                left: p.display_x * 56 + 8,
                top: p.display_y * 56 + 8,
                width: 40,
                height: 40,
                borderRadius: 20,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: p.owner === 1 ? '#ffccc7' : '#d9d9d9',
                border: selectedPieceId === p.id ? '2px solid #1677ff' : '1px solid #8c8c8c',
                opacity: can === false ? 0.5 : 1,
                boxSizing: 'border-box',
              }}
              title={can === false ? (p.commandability.viewer_disabled_reason || 'not commandable') : ''}
            >
              {p.kind}
            </div>
          )
        })}
      </div>
    </div>
  )
}
