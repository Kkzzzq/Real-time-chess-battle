import type { UnlockSchema } from '../../types/contracts'

export function UnlockPanel({ unlock, seat, onChoose, loading }: { unlock?: UnlockSchema; seat?: number; onChoose: (kind: string) => void; loading?: boolean }) {
  if (!unlock) return null
  const me = seat ? unlock.players[String(seat)] : undefined
  const canChoose = !!me?.can_choose_now
  return (
    <div style={{ margin: '8px 0', padding: 8, border: '1px solid #ddd' }}>
      <strong>Unlock</strong> window={String(unlock.window_open)} wave={unlock.current_wave} remaining={unlock.current_wave_remaining_ms ?? '-'}
      <div>状态：{canChoose ? '可选择' : me?.waiting_for_timeout ? '等待结算' : '当前不可选择'} / source={me?.choice_source ?? '-'}</div>
      <div>已解锁：{me?.unlocked?.join(', ') || '-'}</div>
      <div>可选：{me?.available_options?.join(', ') || '-'}</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {(me?.available_options || []).map((k) => (
          <button key={k} disabled={!canChoose || loading} onClick={() => onChoose(k)}>{k}</button>
        ))}
      </div>
    </div>
  )
}
