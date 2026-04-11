import type { MatchSnapshot } from '../../types/contracts'

export function PhasePanel({ snapshot }: { snapshot?: MatchSnapshot }) {
  return <div>
    Phase: {snapshot?.phase.name} ({snapshot?.phase.remaining_ms ?? '-'}ms) wave={snapshot?.unlock.current_wave} next={snapshot?.phase.next_phase_name ?? '-'}
  </div>
}
