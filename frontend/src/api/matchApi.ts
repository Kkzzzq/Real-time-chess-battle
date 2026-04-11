import { apiFetch } from './http'
import type { MatchCreated, PlayerJoin } from '../types/contracts'

export const matchApi = {
  createMatch: (payload?: { ruleset_name?: string; allow_draw?: boolean; tick_ms?: number; custom_unlock_windows?: number[] }) =>
    apiFetch<MatchCreated>('/matches', { method: 'POST', body: JSON.stringify(payload || {}) }),
  listMatches: () => apiFetch<Array<{ match_id: string; status: string; players: Record<string, unknown> }>>('/matches'),
  joinMatch: (matchId: string, playerName: string) => apiFetch<{ player: PlayerJoin; status: string }>(`/matches/${matchId}/join`, { method: 'POST', body: JSON.stringify({ player_name: playerName }) }),
  reconnect: (matchId: string, playerId: string, playerToken: string) => apiFetch<{ player: PlayerJoin; status: string }>(`/matches/${matchId}/reconnect`, { method: 'POST', body: JSON.stringify({ player_id: playerId, player_token: playerToken }) }),
  ready: (matchId: string, playerId: string, playerToken: string) => apiFetch(`/matches/${matchId}/ready`, { method: 'POST', body: JSON.stringify({ player_id: playerId, player_token: playerToken }) }),
  start: (matchId: string) => apiFetch(`/matches/${matchId}/start`, { method: 'POST' }),
  leave: (matchId: string, playerId: string, playerToken: string) => apiFetch(`/matches/${matchId}/leave`, { method: 'POST', body: JSON.stringify({ player_id: playerId, player_token: playerToken }) })
}
