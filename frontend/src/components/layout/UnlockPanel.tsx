import type { UnlockSchema } from '../../types/contracts'

export function UnlockPanel({ unlock, seat, onChoose, loading }: { unlock?: UnlockSchema; seat?: number; onChoose: (kind: string) => void; loading?: boolean }) {
  if (!unlock) return null
  const me = seat ? unlock.players[String(seat)] : undefined
  const canChoose = !!me?.can_choose_now
  const statusText = me?.auto_selected
    ? '已自动选择'
    : me?.has_chosen
      ? '本波已选择，等待结算'
      : canChoose
        ? '可手动选择'
        : unlock.fully_unlocked
          ? '全部兵种已解锁'
          : '当前不可选择'
  return (
    <div style={{ margin: '8px 0', padding: 8, border: '1px solid #ddd' }}>
      <strong>Unlock</strong> window={String(unlock.window_open)} wave={unlock.current_wave} remaining={unlock.current_wave_remaining_ms ?? '-'}
      <div>状态：{statusText} / source={me?.choice_source ?? '-'}</div>
      <div>下一波：{unlock.next_wave_index ?? '-'} @ {unlock.next_wave_start_ms ?? '-'}</div>
      <div>已解锁：{me?.unlocked?.join(', ') || '-'}</div>
      <div>可选：{me?.available_options?.join(', ') || '-'}</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {(me?.available_options || []).map((k) => (
          <button key={k} disabled={!canChoose || loading} style={{ opacity: (!canChoose || loading) ? 0.6 : 1 }} onClick={() => onChoose(k)}>{loading ? '提交中...' : k}</button>
        ))}
      </div>
    </div>
  )
}
