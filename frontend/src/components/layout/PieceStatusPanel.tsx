import type { PieceSchema } from '../../types/contracts'

export function PieceStatusPanel({ pieces }: { pieces: PieceSchema[] }) {
  return <div style={{ marginTop: 8, border: '1px solid #eee', padding: 6 }}>
    <strong>Pieces Status</strong>
    <ul>{pieces.filter(p=>p.alive).slice(0,12).map((p)=><li key={p.id}>{p.id} move={p.move_remaining_ms} cd={p.cooldown_remaining_ms} can={String(p.commandability.viewer_can_command)} reason={p.commandability.viewer_disabled_reason || '-'}</li>)}</ul>
  </div>
}
