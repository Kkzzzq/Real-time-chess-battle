import { apiFetch } from './http'
import type { MatchSnapshot, PhaseSchema, UnlockSchema, BoardSchema, PlayerSchema, EventSchema } from '../types/contracts'

const qs = (playerId: string, playerToken: string) => `?player_id=${encodeURIComponent(playerId)}&player_token=${encodeURIComponent(playerToken)}`

export const queryApi = {
  state: (matchId: string, playerId: string, playerToken: string) => apiFetch<MatchSnapshot>(`/matches/${matchId}/state${qs(playerId, playerToken)}`),
  legalMoves: (matchId: string, pieceId: string, playerId: string, playerToken: string) => apiFetch<{ static: { targets: [number, number][] }; actionable: { actionable_targets: [number, number][] } | null }>(`/matches/${matchId}/pieces/${pieceId}/legal-moves${qs(playerId, playerToken)}`),
  phase: (matchId: string, playerId: string, playerToken: string) => apiFetch<PhaseSchema>(`/matches/${matchId}/phase${qs(playerId, playerToken)}`),
  unlockState: (matchId: string, playerId: string, playerToken: string) => apiFetch<UnlockSchema>(`/matches/${matchId}/unlock-state${qs(playerId, playerToken)}`),
  events: (matchId: string, playerId: string, playerToken: string) => apiFetch<EventSchema[]>(`/matches/${matchId}/events${qs(playerId, playerToken)}`),
  board: (matchId: string, playerId: string, playerToken: string) => apiFetch<{ board: BoardSchema; runtime_board: BoardSchema }>(`/matches/${matchId}/board${qs(playerId, playerToken)}`),
  players: (matchId: string, playerId: string, playerToken: string) => apiFetch<Record<string, PlayerSchema>>(`/matches/${matchId}/players${qs(playerId, playerToken)}`)
}
