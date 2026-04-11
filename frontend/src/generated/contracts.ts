/* eslint-disable */
// Generated from docs/contracts/openapi.json

export type BoardCellSchema = {
  occupants: BoardOccupantSchema[];
  primary_occupant: unknown;
}

export type BoardOccupantSchema = {
  piece_id: string;
  owner: number;
  kind: string;
  moving: boolean;
}

export type BoardSchema = {
  mode: "logical" | "runtime";
  cells: BoardCellSchema[][];
  stats: BoardStatsSchema;
}

export type BoardStatsSchema = {
  alive_total: number;
  alive_by_player: Record<string, unknown>;
}

export type CommandLogSchema = {
  type: string;
  ts: number;
  player_id: string;
  player?: unknown;
  piece_id?: unknown;
  target?: unknown;
  kind?: unknown;
}

export type CommandResultResponse = {
  ok: boolean;
  message: string;
  snapshot: MatchSnapshotResponse;
}

export type CreateMatchRequest = {
  ruleset_name?: string;
  allow_draw?: boolean;
  tick_ms?: number;
  custom_unlock_windows?: unknown;
}

export type EventSchema = {
  type: string;
  ts_ms: number;
  payload: Record<string, unknown>;
}

export type HTTPValidationError = {
  detail?: ValidationError[];
}

export type JoinMatchRequest = {
  player_name: string;
}

export type JoinMatchResponse = {
  player: PlayerJoinResponse;
  status: string;
}

export type LeaveMatchRequest = {
  player_id: string;
  player_token: string;
}

export type LegalMovesActionableSchema = {
  viewer_seat: unknown;
  actionable_targets: unknown[][];
  executable: boolean;
  actionable_context: string;
  reason: unknown;
}

export type LegalMovesResponse = {
  piece_id: string;
  owner: number;
  player_id: unknown;
  static: LegalMovesStaticSchema;
  actionable: unknown;
}

export type LegalMovesStaticSchema = {
  targets: unknown[][];
}

export type MatchCreatedResponse = {
  match_id: string;
  status: string;
  ruleset: Record<string, unknown>;
}

export type MatchMetaSchema = {
  match_id: string;
  status: string;
  winner: unknown;
  reason: unknown;
  created_at: number;
  started_at: unknown;
  now_ms: number;
  version: number;
  ruleset: Record<string, unknown>;
}

export type MatchSnapshotResponse = {
  match_meta: MatchMetaSchema;
  players: Record<string, unknown>;
  phase: PhaseSchema;
  unlock: UnlockSchema;
  board: BoardSchema;
  runtime_board: BoardSchema;
  pieces: PieceSchema[];
  events: EventSchema[];
  command_log: CommandLogSchema[];
}

export type MatchStatusResponse = {
  ok: boolean;
  status: string;
  players?: unknown;
}

export type MoveCommandRequest = {
  player_id: string;
  player_token: string;
  piece_id: string;
  target_x: number;
  target_y: number;
}

export type PhaseSchema = {
  name: string;
  deadline_ms: unknown;
  remaining_ms: unknown;
  wave_index: number;
  next_phase_name: unknown;
  next_phase_start_ms: unknown;
  next_wave_index: unknown;
  next_wave_start_ms: unknown;
  current_wave_start_ms: unknown;
  current_wave_deadline_ms: unknown;
}

export type PieceCommandabilitySchema = {
  owner_can_command: boolean;
  owner_disabled_reason: unknown;
  viewer_can_command?: unknown;
  viewer_disabled_reason?: unknown;
  note: string;
}

export type PieceSchema = {
  id: string;
  owner: number;
  kind: string;
  x: number;
  y: number;
  display_x: number;
  display_y: number;
  alive: boolean;
  is_moving: boolean;
  target_x: number;
  target_y: number;
  path: unknown[][];
  move_start_at: unknown;
  move_end_at: unknown;
  move_remaining_ms: number;
  cooldown_remaining_ms: number;
  can_command: boolean;
  disabled_reason: unknown;
  can_command_scope: string;
  commandability: PieceCommandabilitySchema;
  runtime_cells: unknown[][];
  segment: PieceSegmentSchema;
  captured_at: unknown;
  death_reason: unknown;
}

export type PieceSegmentSchema = {
  index: number;
  start: unknown[];
  end: unknown[];
  local_progress: number;
}

export type PieceType = "soldier" | "advisor" | "elephant" | "horse" | "cannon" | "chariot" | "general"

export type PlayerJoinResponse = {
  seat: number;
  player_id: string;
  player_token: string;
  player_token_expires_at?: unknown;
  name: string;
  ready: boolean;
  online: boolean;
  is_host: boolean;
}

export type PlayerSchema = {
  seat: number;
  player_id: string;
  player_token?: unknown;
  name: string;
  ready: boolean;
  online: boolean;
  is_host: boolean;
}

export type ReadyMatchRequest = {
  player_id: string;
  player_token: string;
}

export type ReconnectMatchRequest = {
  player_id: string;
  player_token: string;
}

export type ReconnectMatchResponse = {
  player: PlayerJoinResponse;
  status: string;
}

export type ResignRequest = {
  player_id: string;
  player_token: string;
}

export type StartMatchRequest = {
  player_id: string;
  player_token: string;
}

export type StartMatchResponse = {
  ok: boolean;
  status: string;
  started_at: number;
  snapshot: MatchSnapshotResponse;
}

export type UnlockCommandRequest = {
  player_id: string;
  player_token: string;
  kind: PieceType;
}

export type UnlockPlayerSchema = {
  unlocked: string[];
  available_options: string[];
  wave_choice: unknown;
  has_chosen: boolean;
  auto_selected: boolean;
  can_choose_now: boolean;
  waiting_for_timeout: boolean;
  choice_source: "manual" | "auto" | "none";
}

export type UnlockSchema = {
  phase: string;
  fully_unlocked: boolean;
  window_open: boolean;
  current_wave: number;
  wave_start_ms: unknown;
  wave_deadline_ms: unknown;
  current_wave_remaining_ms: unknown;
  wave_timeout: boolean;
  wave_options: string[];
  next_wave_index: unknown;
  next_wave_start_ms: unknown;
  players: Record<string, unknown>;
}

export type ValidationError = {
  loc: unknown[];
  msg: string;
  type: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}
