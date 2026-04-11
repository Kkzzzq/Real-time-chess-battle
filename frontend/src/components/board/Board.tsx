import type { MatchSnapshot } from '../../types/contracts'

type Props = {
  snapshot?: MatchSnapshot
  selectedPieceId?: string
  actionableTargets: [number, number][]
  onCellClick: (x: number, y: number) => void
  onPieceClick: (pieceId: string) => void
  showRuntimeDebug?: boolean
}

export function Board({ snapshot, selectedPieceId, actionableTargets, onCellClick, onPieceClick, showRuntimeDebug = false }: Props) {
  const runtimeCells = snapshot?.runtime_board.cells
  const pieces = snapshot?.pieces.filter((p) => p.alive) || []
  const isTarget = (x: number, y: number) => actionableTargets.some(([tx, ty]) => tx === x && ty === y)

  const handleCell = (x: number, y: number, primaryId?: string) => {
    if (selectedPieceId) {
      // when a piece is already selected, clicking any cell (including occupied) means try move/capture
      onCellClick(x, y)
      return
    }
    if (primaryId) onPieceClick(primaryId)
    else onCellClick(x, y)
  }

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
                opacity: can === false ? 0.45 : 1,
                boxSizing: 'border-box',
                transition: 'left 160ms linear, top 160ms linear, opacity 140ms ease, transform 140ms ease',
                transform: p.is_moving ? 'scale(1.04)' : 'scale(1)',
                boxShadow: p.cooldown_remaining_ms > 0 ? '0 0 0 2px rgba(250,140,22,0.35)' : 'none',
              }}
              title={can === false ? (p.commandability.viewer_disabled_reason || 'not commandable') : ''}
            >
              {p.kind}
            </div>
          )
        })}
      </div>
      {showRuntimeDebug ? (
        <pre style={{ position: 'absolute', right: 0, bottom: 0, width: 220, maxHeight: 140, overflow: 'auto', margin: 0, background: 'rgba(0,0,0,0.55)', color: '#fff', fontSize: 10 }}>
          {JSON.stringify(snapshot?.runtime_board?.stats || {}, null, 2)}
        </pre>
      ) : null}
    </div>
  )
}
