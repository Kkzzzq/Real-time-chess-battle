import type { MatchSnapshot } from '../../types/contracts'

type Props = { snapshot?: MatchSnapshot; enabled?: boolean }

export function BoardDebugOverlay({ snapshot, enabled = false }: Props) {
  if (!enabled) return null
  return (
    <pre style={{ position: 'absolute', right: 0, bottom: 0, width: 220, maxHeight: 140, overflow: 'auto', margin: 0, background: 'rgba(0,0,0,0.55)', color: '#fff', fontSize: 10 }}>
      {JSON.stringify(snapshot?.runtime_board?.stats || {}, null, 2)}
    </pre>
  )
}
