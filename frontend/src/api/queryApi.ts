import { apiFetch } from './http'
import type { MatchSnapshot, PhaseSchema, UnlockSchema, BoardSchema, PlayerSchema, EventSchema } from '../types/contracts'

const qs = (playerId?: string, playerToken?: string) => (playerId && playerToken ? `?player_id=${playerId}&player_token=${playerToken}` : '')

export const queryApi = {
  state: (matchId: string, playerId?: string, playerToken?: string) => apiFetch<MatchSnapshot>(`/matches/${matchId}/state${qs(playerId, playerToken)}`),
  legalMoves: (matchId: string, pieceId: string, playerId?: string, playerToken?: string) => apiFetch<{ static: { targets: [number, number][] }; actionable: { actionable_targets: [number, number][] } | null }>(`/matches/${matchId}/pieces/${pieceId}/legal-moves${qs(playerId, playerToken)}`),
  phase: (matchId: string) => apiFetch<PhaseSchema>(`/matches/${matchId}/phase`),
  unlockState: (matchId: string) => apiFetch<UnlockSchema>(`/matches/${matchId}/unlock-state`),
  events: (matchId: string) => apiFetch<EventSchema[]>(`/matches/${matchId}/events`),
  board: (matchId: string) => apiFetch<{ board: BoardSchema; runtime_board: BoardSchema }>(`/matches/${matchId}/board`),
  players: (matchId: string) => apiFetch<Record<string, PlayerSchema>>(`/matches/${matchId}/players`)
}
