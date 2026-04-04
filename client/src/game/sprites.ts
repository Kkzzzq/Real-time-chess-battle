
/**
 * Sprite loader for Real-time-chess-battle（中国象棋）.
 *
 * 当前继续复用旧 sprite sheet 作为临时占位纹理：
 * - 兵/卒 -> Pawn
 * - 马 -> Knight
 * - 象 -> Bishop
 * - 车 -> Rook
 * - 士 -> Queen
 * - 将/帅 -> King
 * - 炮 -> Rook（临时占位）
 */

import { Assets, Texture, Rectangle } from 'pixi.js';
import chessSpritesUrl from '../assets/chess-sprites.png';

export type PieceType = 'P' | 'N' | 'E' | 'R' | 'A' | 'G' | 'C' | 'B' | 'Q' | 'K';

type LegacySpriteType = 'P' | 'N' | 'B' | 'R' | 'Q' | 'K';

const PIECE_TEXTURE_MAP: Record<PieceType, LegacySpriteType> = {
  P: 'P',
  N: 'N',
  E: 'B',
  R: 'R',
  A: 'Q',
  G: 'K',
  C: 'R',
  B: 'B',
  Q: 'Q',
  K: 'K',
};

const SPRITE_SIZE = 100;
const OUTLINE_SPRITE_COORDS: Record<LegacySpriteType, { x: number; y: number }> = {
  P: { x: 45, y: 19 },
  N: { x: 145, y: 15 },
  B: { x: 248, y: 16 },
  R: { x: 346, y: 13 },
  Q: { x: 445, y: 13 },
  K: { x: 545, y: 15 },
};
const FILLED_SPRITE_COORDS: Record<LegacySpriteType, { x: number; y: number }> = {
  P: { x: 45, y: 117 },
  N: { x: 145, y: 115 },
  B: { x: 248, y: 115 },
  R: { x: 348, y: 115 },
  Q: { x: 446, y: 115 },
  K: { x: 545, y: 115 },
};

export const PLAYER_COLORS: Record<number, number> = {
  1: 0xc62828,
  2: 0x1a1a1a,
  3: 0xe63946,
  4: 0x457b9d,
};

const spriteTextures: Map<string, Texture> = new Map();
let loaded = false;

function getTextureKey(pieceType: LegacySpriteType, style: 'outline' | 'filled'): string {
  return `piece_${pieceType}_${style}`;
}

export async function loadSprites(): Promise<void> {
  if (loaded) return;
  const texture = await Assets.load<Texture>(chessSpritesUrl);
  const baseTexture = texture.source;
  for (const [pieceType, coords] of Object.entries(OUTLINE_SPRITE_COORDS)) {
    const frame = new Rectangle(coords.x, coords.y, SPRITE_SIZE, SPRITE_SIZE);
    spriteTextures.set(getTextureKey(pieceType as LegacySpriteType, 'outline'), new Texture({ source: baseTexture, frame }));
  }
  for (const [pieceType, coords] of Object.entries(FILLED_SPRITE_COORDS)) {
    const frame = new Rectangle(coords.x, coords.y, SPRITE_SIZE, SPRITE_SIZE);
    spriteTextures.set(getTextureKey(pieceType as LegacySpriteType, 'filled'), new Texture({ source: baseTexture, frame }));
  }
  loaded = true;
}

export function getPieceTexture(pieceType: PieceType, player: number = 1): Texture {
  const mapped = PIECE_TEXTURE_MAP[pieceType] ?? 'P';
  const style = player === 2 ? 'filled' : 'outline';
  const key = getTextureKey(mapped, style);
  const texture = spriteTextures.get(key);
  if (!texture) {
    throw new Error(`Texture not found for piece type: ${pieceType}, mapped: ${mapped}.`);
  }
  return texture;
}

export function getPlayerTint(player: number): number {
  return PLAYER_COLORS[player] ?? 0xffffff;
}

export function areSpritesLoaded(): boolean {
  return loaded;
}
