import type { MatchSnapshot } from '../../types/contracts'

type Props = { snapshot?: MatchSnapshot }

export function BoardCellOverlay({ snapshot }: Props) {
  const runtimeCells = snapshot?.runtime_board.cells
  if (!runtimeCells) return null

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {Array.from({ length: 10 }).flatMap((_, y) =>
        Array.from({ length: 9 }).map((__, x) => {
          const cell = runtimeCells[y]?.[x]
          const count = cell?.occupants.length || 0
          if (count < 2) return null
          return (
            <div key={`ov-${x}-${y}`} style={{ position: 'absolute', left: x * 56 + 2, top: y * 56 + 2, fontSize: 10, color: '#a8071a', fontWeight: 700 }}>
              {count}x
            </div>
          )
        })
      )}
    </div>
  )
}
