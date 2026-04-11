export type Seat = 1 | 2

export interface MatchMeta { match_id: string; status: 'waiting'|'running'|'ended'|string; winner: number | null; reason: string | null; created_at: number; started_at: number | null; now_ms: number; version: number; ruleset: { ruleset_name: string; allow_draw: boolean; tick_ms: number; custom_unlock_windows: number[] | null } }
export interface PlayerSchema { seat: number; player_id: string; name: string; ready: boolean; online: boolean; is_host: boolean }
export interface PhaseSchema { name: string; deadline_ms: number | null; remaining_ms: number | null; wave_index: number; next_phase_name: string | null; next_phase_start_ms: number | null; next_wave_index: number | null; next_wave_start_ms: number | null; current_wave_start_ms: number | null; current_wave_deadline_ms: number | null }
export interface UnlockPlayerSchema { unlocked: string[]; available_options: string[]; wave_choice: string | null; has_chosen: boolean; auto_selected: boolean; can_choose_now: boolean; waiting_for_timeout: boolean; choice_source: 'manual'|'auto'|'none' }
export interface UnlockSchema { phase: string; fully_unlocked: boolean; window_open: boolean; current_wave: number; wave_start_ms: number | null; wave_deadline_ms: number | null; current_wave_remaining_ms: number | null; wave_timeout: boolean; wave_options: string[]; next_wave_index: number | null; next_wave_start_ms: number | null; players: Record<string, UnlockPlayerSchema> }
export interface BoardOccupant { piece_id: string; owner: number; kind: string; moving: boolean }
export interface BoardCell { occupants: BoardOccupant[]; primary_occupant: BoardOccupant | null }
export interface BoardSchema { mode: 'logical'|'runtime'; cells: BoardCell[][]; stats: { alive_total: number; alive_by_player: Record<string, number> } }
export interface PieceCommandability { owner_can_command: boolean; owner_disabled_reason: string | null; viewer_can_command: boolean | null; viewer_disabled_reason: string | null; note: string }
export interface PieceSegment { index: number; start: [number, number]; end: [number, number]; local_progress: number }
export interface PieceSchema { id: string; owner: number; kind: string; x: number; y: number; display_x: number; display_y: number; alive: boolean; is_moving: boolean; target_x: number; target_y: number; path: [number, number][]; move_start_at: number | null; move_end_at: number | null; move_remaining_ms: number; cooldown_remaining_ms: number; can_command: boolean; disabled_reason: string | null; can_command_scope: string; commandability: PieceCommandability; runtime_cells: [number, number][]; segment: PieceSegment; captured_at: number | null; death_reason: string | null }
export interface EventSchema { type: string; ts_ms: number; payload: Record<string, unknown> }
export interface CommandLogSchema { type: string; ts: number; player_id: string; player: number | null; piece_id: string | null; target: [number, number] | null; kind: string | null }
export interface MatchSnapshot { match_meta: MatchMeta; players: Record<string, PlayerSchema>; phase: PhaseSchema; unlock: UnlockSchema; board: BoardSchema; runtime_board: BoardSchema; pieces: PieceSchema[]; events: EventSchema[]; command_log: CommandLogSchema[] }

export interface PlayerJoin { seat: Seat; player_id: string; player_token: string; player_token_expires_at?: number | null; name: string; ready: boolean; online: boolean; is_host: boolean }
export interface MatchCreated { match_id: string; status: string; ruleset: MatchMeta['ruleset'] }
