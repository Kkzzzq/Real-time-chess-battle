/**
 * Game Constants for Real-time-chess-battle（中国象棋前端）
 */

import type { BoardType } from '../api/types';

export const BOARD_COLORS = {
  light: 0xf5e6c8,
  dark: 0xe8d3ad,
  highlight: 0xf0c94b,
  legalMove: 0x93c47d,
  selected: 0xf6b26b,
  invalid: 0x999999,
  background: 0xfcf8ef,
} as const;

export const BOARD_DIMENSIONS: Record<BoardType, { width: number; height: number }> = {
  standard: { width: 9, height: 10 },
} as const;

const TICK_RATE_HZ = 30;

export const TIMING = {
  TICK_RATE_HZ,
  TICK_PERIOD_MS: 1000 / TICK_RATE_HZ,
  TICKS_PER_SECOND: TICK_RATE_HZ,
  STANDARD_SECONDS_PER_SQUARE: 1.0,
  LIGHTNING_SECONDS_PER_SQUARE: 0.2,
  STANDARD_COOLDOWN_SECONDS: 10.0,
  LIGHTNING_COOLDOWN_SECONDS: 2.0,
  get STANDARD_TICKS_PER_SQUARE() {
    return Math.round(this.STANDARD_SECONDS_PER_SQUARE * TICK_RATE_HZ);
  },
  get LIGHTNING_TICKS_PER_SQUARE() {
    return Math.round(this.LIGHTNING_SECONDS_PER_SQUARE * TICK_RATE_HZ);
  },
  get STANDARD_COOLDOWN_TICKS() {
    return Math.round(this.STANDARD_COOLDOWN_SECONDS * TICK_RATE_HZ);
  },
  get LIGHTNING_COOLDOWN_TICKS() {
    return Math.round(this.LIGHTNING_COOLDOWN_SECONDS * TICK_RATE_HZ);
  },
} as const;

export const RENDER = {
  SQUARE_SIZE: 64,
  PIECE_SCALE: 0.9,
  PIECE_OFFSET_X: 0,
  PIECE_OFFSET_Y: 0,
  HIGHLIGHT_ALPHA: 0.35,
  LEGAL_MOVE_ALPHA: 0.4,
  COOLDOWN_ALPHA: 0.5,
} as const;

export function isCornerSquare(_row: number, _col: number): boolean {
  return false;
}

export function isValidSquare(row: number, col: number, boardType: BoardType = 'standard'): boolean {
  const dims = BOARD_DIMENSIONS[boardType];
  return row >= 0 && row < dims.height && col >= 0 && col < dims.width;
}

export function getSquareColor(row: number, col: number, _boardType: BoardType = 'standard'): number {
  return (row + col) % 2 === 0 ? BOARD_COLORS.light : BOARD_COLORS.dark;
}

export function getPieceRotation(player: number, _boardType: BoardType = 'standard'): number {
  return player === 2 ? Math.PI : 0;
}

export interface Coords {
  row: number;
  col: number;
}

export function transformToViewCoords(coords: Coords, playerNumber: number, boardType: BoardType = 'standard'): Coords {
  const { row, col } = coords;
  const dims = BOARD_DIMENSIONS[boardType];
  if (playerNumber === 2) {
    return { row: dims.height - 1 - row, col: dims.width - 1 - col };
  }
  return { row, col };
}

export function transformToGameCoords(coords: Coords, playerNumber: number, boardType: BoardType = 'standard'): Coords {
  const { row, col } = coords;
  const dims = BOARD_DIMENSIONS[boardType];
  if (playerNumber === 2) {
    return { row: dims.height - 1 - row, col: dims.width - 1 - col };
  }
  return { row, col };
}
