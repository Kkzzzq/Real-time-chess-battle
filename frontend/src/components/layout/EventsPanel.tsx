import type { EventSchema } from '../../types/contracts'

const eventCopy = (e: EventSchema) => {
  const seat = (e.payload?.seat as number | undefined)
  const pid = (e.payload?.player_id as string | undefined)
  switch (e.type) {
    case 'player_joined':
      return `玩家 ${e.payload?.name || '-'} 加入（seat ${seat ?? '-' }）`
    case 'player_ready':
      return `玩家已准备（seat ${seat ?? '-'}）`
    case 'match_started':
      return '对局开始'
    case 'unlock_chosen':
      return `玩家解锁：${String(e.payload?.kind || '-')}`
    case 'unlock_auto_applied':
      return `超时自动解锁：${String(e.payload?.kind || '-')}`
    case 'move_started':
      return `移动开始：${String(e.payload?.piece_id || '-')}`
    case 'capture':
      return `吃子：${String(e.payload?.attacker_piece_id || '-')}`
    case 'resign':
      return `认输（player ${pid || '-'})`
    case 'match_ended':
      return `对局结束（原因：${String(e.payload?.reason || 'unknown')}）`
    default:
      return e.type
  }
}

export function EventsPanel({ events, debug = false }: { events: EventSchema[]; debug?: boolean }) {
  return <div style={{ maxHeight: 180, overflow: 'auto', border: '1px solid #eee', padding: 6, marginTop: 8 }}>
    <strong>Events</strong>
    <ul>{events.slice(-20).map((e, idx) => <li key={idx}>
      {eventCopy(e)} @ {new Date(e.ts_ms).toLocaleTimeString()}
      {debug ? <pre style={{ margin: '4px 0', whiteSpace: 'pre-wrap' }}>{JSON.stringify(e.payload, null, 2)}</pre> : null}
    </li>)}</ul>
  </div>
}
