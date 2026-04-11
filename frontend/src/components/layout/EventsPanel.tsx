import type { EventSchema } from '../../types/contracts'

const mapEvent = (e: EventSchema) => {
  const zh: Record<string, string> = {
    player_joined: '玩家加入',
    player_ready: '玩家准备',
    match_started: '对局开始',
    unlock_chosen: '解锁选择',
    unlock_auto_applied: '自动解锁',
    move_started: '移动开始',
    move_finished: '移动结束',
    match_ended: '对局结束',
  }
  return zh[e.type] || e.type
}

export function EventsPanel({ events }: { events: EventSchema[] }) {
  return <div style={{ maxHeight: 180, overflow: 'auto', border: '1px solid #eee', padding: 6, marginTop: 8 }}>
    <strong>Events</strong>
    <ul>{events.slice(-20).map((e, idx) => <li key={idx}>{mapEvent(e)} @ {e.ts_ms}</li>)}</ul>
  </div>
}
