/**
 * WebSocket Protocol Types
 * 第一版协议收口为：双人中国象棋（无升变、无四人棋）
 */

export type XiangqiPieceType = 'P' | 'N' | 'E' | 'R' | 'A' | 'G' | 'C';

export interface WsPieceState {
  id: string;
  row: number;
  col: number;
  captured: boolean;
  type?: XiangqiPieceType;
  player?: number;
  moving?: boolean;
  on_cooldown?: boolean;
  moved?: boolean;
}

export interface WsActiveMove {
  piece_id: string;
  path: [number, number][];
  start_tick: number;
  progress?: number;
}

export interface WsCooldown {
  piece_id: string;
  remaining_ticks: number;
}

export interface WsCaptureEvent {
  type: 'capture';
  capturer: string;
  captured: string;
  tick: number;
}

export type WsGameEvent = WsCaptureEvent;

export interface CampaignLevelInfo {
  level_id: number;
  title: string;
  description: string;
  has_next_level: boolean;
}

export interface JoinedMessage {
  type: 'joined';
  player_number: number; // 0 = spectator, 1-2 = player
  tick_rate_hz: number;
  campaign_level: CampaignLevelInfo | null;
}

export interface StateUpdateMessage {
  type: 'state';
  tick: number;
  pieces: WsPieceState[];
  active_moves: WsActiveMove[];
  cooldowns: WsCooldown[];
  events: WsGameEvent[];
  time_since_tick?: number;
}

export interface CountdownMessage {
  type: 'countdown';
  seconds: number;
}

export interface GameStartedMessage {
  type: 'game_started';
  tick: number;
}

export interface GameOverMessage {
  type: 'game_over';
  winner: number; // 0 for draw, 1-2 for player
  reason: 'general_captured' | 'draw_timeout' | 'resignation' | 'draw';
}

export interface RatingChangePayload {
  old_rating: number;
  new_rating: number;
  old_belt: string;
  new_belt: string;
  belt_changed: boolean;
}

export interface RatingUpdateMessage {
  type: 'rating_update';
  ratings: Record<string, RatingChangePayload>;
}

export interface MoveRejectedMessage {
  type: 'move_rejected';
  piece_id: string;
  reason: string;
}

export interface PongMessage {
  type: 'pong';
}

export interface DrawOfferedMessage {
  type: 'draw_offered';
  player: number;
  draw_offers: number[];
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export type ServerMessage =
  | JoinedMessage
  | StateUpdateMessage
  | CountdownMessage
  | GameStartedMessage
  | GameOverMessage
  | RatingUpdateMessage
  | MoveRejectedMessage
  | DrawOfferedMessage
  | PongMessage
  | ErrorMessage;

export interface MoveClientMessage {
  type: 'move';
  piece_id: string;
  to_row: number;
  to_col: number;
}

export interface ReadyClientMessage {
  type: 'ready';
}

export interface ResignClientMessage {
  type: 'resign';
}

export interface OfferDrawClientMessage {
  type: 'offer_draw';
}

export interface PingClientMessage {
  type: 'ping';
}

export type ClientMessage =
  | MoveClientMessage
  | ReadyClientMessage
  | ResignClientMessage
  | OfferDrawClientMessage
  | PingClientMessage;

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

export interface WebSocketClientOptions {
  gameId: string;
  playerKey?: string;
  onJoined?: (msg: JoinedMessage) => void;
  onStateUpdate?: (msg: StateUpdateMessage) => void;
  onCountdown?: (msg: CountdownMessage) => void;
  onGameStarted?: (msg: GameStartedMessage) => void;
  onGameOver?: (msg: GameOverMessage) => void;
  onRatingUpdate?: (msg: RatingUpdateMessage) => void;
  onDrawOffered?: (msg: DrawOfferedMessage) => void;
  onMoveRejected?: (msg: MoveRejectedMessage) => void;
  onError?: (msg: ErrorMessage) => void;
  onConnectionChange?: (state: ConnectionState) => void;
  onReconnected?: () => void;
}
