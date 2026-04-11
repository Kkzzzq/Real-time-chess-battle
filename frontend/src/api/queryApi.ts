import { apiFetch } from './http'
import type { MatchSnapshot } from '../types/contracts'

export const queryApi = {
  state: (matchId: string, playerId?: string, playerToken?: string) => {
    const q = playerId && playerToken ? `?player_id=${playerId}&player_token=${playerToken}` : ''
    return apiFetch<MatchSnapshot>(`/matches/${matchId}/state${q}`)
  },
  legalMoves: (matchId: string, pieceId: string, playerId?: string, playerToken?: string) => {
    const q = playerId && playerToken ? `?player_id=${playerId}&player_token=${playerToken}` : ''
    return apiFetch<{ static: { targets: [number, number][] }; actionable: { actionable_targets: [number, number][] } | null }>(`/matches/${matchId}/pieces/${pieceId}/legal-moves${q}`)
  }
}
