import type { MatchSnapshot } from '../../types/contracts'

type Props = { snapshot?: MatchSnapshot; selectedPieceId?: string }

export function PieceLayer({ snapshot, selectedPieceId }: Props) {
  const pieces = snapshot?.pieces.filter((p) => p.alive) || []

  return (
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
  )
}
