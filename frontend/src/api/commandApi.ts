import { apiFetch } from './http'

export const commandApi = {
  move: (matchId: string, payload: { player_id: string; player_token: string; piece_id: string; target_x: number; target_y: number }) => apiFetch(`/matches/${matchId}/commands/move`, { method: 'POST', body: JSON.stringify(payload) }),
  unlock: (matchId: string, payload: { player_id: string; player_token: string; kind: string }) => apiFetch(`/matches/${matchId}/commands/unlock`, { method: 'POST', body: JSON.stringify(payload) }),
  resign: (matchId: string, payload: { player_id: string; player_token: string }) => apiFetch(`/matches/${matchId}/commands/resign`, { method: 'POST', body: JSON.stringify(payload) })
}
