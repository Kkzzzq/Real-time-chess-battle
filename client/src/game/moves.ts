
/**
 * Client-side legal move calculation for Real-time-chess-battle（中国象棋）.
 */

import type { Piece, ActiveMove, BoardType } from '../stores/game';
import { BOARD_DIMENSIONS, isValidSquare } from './constants';

function getPieceAtLocation(pieces: Piece[], row: number, col: number): Piece | null {
  return pieces.find((p) => !p.captured && p.row === row && p.col === col) ?? null;
}

function isMoving(activeMoves: ActiveMove[], pieceId: string): boolean {
  return activeMoves.some((m) => m.pieceId === pieceId);
}

function isOccupiedByFriendly(pieces: Piece[], activeMoves: ActiveMove[], piece: Piece, row: number, col: number): boolean {
  const target = getPieceAtLocation(pieces, row, col);
  return !!target && target.player === piece.player && !isMoving(activeMoves, target.id);
}

function countLineBlockers(pieces: Piece[], activeMoves: ActiveMove[], fromRow: number, fromCol: number, toRow: number, toCol: number): number {
  if (fromRow !== toRow && fromCol !== toCol) return -1;
  let count = 0;
  if (fromRow === toRow) {
    const step = toCol > fromCol ? 1 : -1;
    for (let c = fromCol + step; c !== toCol; c += step) {
      const occ = getPieceAtLocation(pieces, fromRow, c);
      if (occ && !isMoving(activeMoves, occ.id)) count++;
    }
  } else {
    const step = toRow > fromRow ? 1 : -1;
    for (let r = fromRow + step; r !== toRow; r += step) {
      const occ = getPieceAtLocation(pieces, r, fromCol);
      if (occ && !isMoving(activeMoves, occ.id)) count++;
    }
  }
  return count;
}

function isPalaceSquare(player: number, row: number, col: number): boolean {
  if (col < 3 || col > 5) return false;
  return player === 1 ? row >= 7 && row <= 9 : row >= 0 && row <= 2;
}

function hasCrossedRiver(player: number, row: number): boolean {
  return player === 1 ? row <= 4 : row >= 5;
}

function generalsFacing(pieces: Piece[], activeMoves: ActiveMove[], movingPiece: Piece, toRow: number, toCol: number): boolean {
  let red: [number, number] | null = null;
  let black: [number, number] | null = null;
  for (const p of pieces) {
    if (p.captured) continue;
    let row = p.row;
    let col = p.col;
    if (p.id === movingPiece.id) {
      row = toRow;
      col = toCol;
    }
    if (p.type === 'G' && p.player === 1) red = [row, col];
    if (p.type === 'G' && p.player === 2) black = [row, col];
  }
  if (!red || !black) return false;
  if (red[1] !== black[1]) return false;
  for (let r = Math.min(red[0], black[0]) + 1; r < Math.max(red[0], black[0]); r++) {
    const occ = getPieceAtLocation(pieces, r, red[1]);
    if (!occ || occ.id === movingPiece.id || isMoving(activeMoves, occ.id)) continue;
    return false;
  }
  return true;
}

function isSoldierMove(piece: Piece, toRow: number, toCol: number): boolean {
  const dr = toRow - piece.row;
  const dc = toCol - piece.col;
  const forward = piece.player === 1 ? -1 : 1;
  if (dr === forward && dc === 0) return true;
  if (hasCrossedRiver(piece.player, piece.row) && dr === 0 && Math.abs(dc) === 1) return true;
  return false;
}

function isHorseMove(pieces: Piece[], activeMoves: ActiveMove[], piece: Piece, toRow: number, toCol: number): boolean {
  const dr = toRow - piece.row;
  const dc = toCol - piece.col;
  if (!((Math.abs(dr) === 2 && Math.abs(dc) === 1) || (Math.abs(dr) === 1 && Math.abs(dc) === 2))) return false;
  const legRow = Math.abs(dr) === 2 ? piece.row + dr / 2 : piece.row;
  const legCol = Math.abs(dc) === 2 ? piece.col + dc / 2 : piece.col;
  const leg = getPieceAtLocation(pieces, legRow, legCol);
  return !(leg && !isMoving(activeMoves, leg.id));
}

function isElephantMove(pieces: Piece[], activeMoves: ActiveMove[], piece: Piece, toRow: number, toCol: number): boolean {
  const dr = toRow - piece.row;
  const dc = toCol - piece.col;
  if (Math.abs(dr) !== 2 || Math.abs(dc) !== 2) return false;
  if (piece.player === 1 && toRow < 5) return false;
  if (piece.player === 2 && toRow > 4) return false;
  const eye = getPieceAtLocation(pieces, piece.row + dr / 2, piece.col + dc / 2);
  return !(eye && !isMoving(activeMoves, eye.id));
}

function isAdvisorMove(piece: Piece, toRow: number, toCol: number): boolean {
  return Math.abs(toRow - piece.row) === 1 && Math.abs(toCol - piece.col) === 1 && isPalaceSquare(piece.player, toRow, toCol);
}

function isGeneralMove(pieces: Piece[], activeMoves: ActiveMove[], piece: Piece, toRow: number, toCol: number): boolean {
  const target = getPieceAtLocation(pieces, toRow, toCol);
  if (target && target.player !== piece.player && target.type === 'G') {
    if (piece.col !== toCol) return false;
    return countLineBlockers(pieces, activeMoves, piece.row, piece.col, toRow, toCol) === 0;
  }
  return Math.abs(toRow - piece.row) + Math.abs(toCol - piece.col) === 1 && isPalaceSquare(piece.player, toRow, toCol);
}

function isChariotMove(pieces: Piece[], activeMoves: ActiveMove[], piece: Piece, toRow: number, toCol: number): boolean {
  return countLineBlockers(pieces, activeMoves, piece.row, piece.col, toRow, toCol) === 0;
}

function isCannonMove(pieces: Piece[], activeMoves: ActiveMove[], piece: Piece, toRow: number, toCol: number): boolean {
  const blockers = countLineBlockers(pieces, activeMoves, piece.row, piece.col, toRow, toCol);
  if (blockers < 0) return false;
  const target = getPieceAtLocation(pieces, toRow, toCol);
  if (!target || isMoving(activeMoves, target.id)) return blockers === 0;
  return target.player !== piece.player && blockers === 1;
}

export function isLegalMove(
  pieces: Piece[],
  activeMoves: ActiveMove[],
  _currentTick: number,
  _ticksPerSquare: number,
  piece: Piece,
  toRow: number,
  toCol: number,
  boardType: BoardType = 'standard'
): boolean {
  const dims = BOARD_DIMENSIONS[boardType];
  if (toRow < 0 || toRow >= dims.height || toCol < 0 || toCol >= dims.width) return false;
  if (!isValidSquare(toRow, toCol, boardType)) return false;
  if (piece.row === toRow && piece.col === toCol) return false;
  if (isOccupiedByFriendly(pieces, activeMoves, piece, toRow, toCol)) return false;

  let ok = false;
  switch (piece.type) {
    case 'P': ok = isSoldierMove(piece, toRow, toCol); break;
    case 'N': ok = isHorseMove(pieces, activeMoves, piece, toRow, toCol); break;
    case 'E': ok = isElephantMove(pieces, activeMoves, piece, toRow, toCol); break;
    case 'R': ok = isChariotMove(pieces, activeMoves, piece, toRow, toCol); break;
    case 'A': ok = isAdvisorMove(piece, toRow, toCol); break;
    case 'G': ok = isGeneralMove(pieces, activeMoves, piece, toRow, toCol); break;
    case 'C': ok = isCannonMove(pieces, activeMoves, piece, toRow, toCol); break;
    default: ok = false;
  }
  if (!ok) return false;
  return !generalsFacing(pieces, activeMoves, piece, toRow, toCol);
}

export function getLegalMovesForPiece(
  pieces: Piece[],
  activeMoves: ActiveMove[],
  currentTick: number,
  ticksPerSquare: number,
  piece: Piece,
  boardType: BoardType = 'standard'
): [number, number][] {
  const dims = BOARD_DIMENSIONS[boardType];
  const moves: [number, number][] = [];
  for (let row = 0; row < dims.height; row++) {
    for (let col = 0; col < dims.width; col++) {
      if (isLegalMove(pieces, activeMoves, currentTick, ticksPerSquare, piece, row, col, boardType)) {
        moves.push([row, col]);
      }
    }
  }
  return moves;
}

export function getAllLegalMoves(
  pieces: Piece[],
  activeMoves: ActiveMove[],
  currentTick: number,
  ticksPerSquare: number,
  playerNumber: number,
  boardType: BoardType = 'standard'
): Map<string, [number, number][]> {
  const allMoves = new Map<string, [number, number][]>();
  for (const piece of pieces) {
    if (piece.player === playerNumber && !piece.captured && !piece.moving && !piece.onCooldown) {
      const moves = getLegalMovesForPiece(pieces, activeMoves, currentTick, ticksPerSquare, piece, boardType);
      if (moves.length > 0) allMoves.set(piece.id, moves);
    }
  }
  return allMoves;
}
