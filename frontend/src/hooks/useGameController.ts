import { commandApi } from '../api/commandApi'
import { queryApi } from '../api/queryApi'
import { useUiStore } from '../store/uiStore'

export function useGameController(matchId: string, playerId?: string, playerToken?: string) {
  const ui = useUiStore()

  const selectPiece = async (pieceId: string) => {
    if (!playerId || !playerToken) return
    const legal = await queryApi.legalMoves(matchId, pieceId, playerId, playerToken)
    ui.setSelection(pieceId, legal.actionable?.actionable_targets || [])
  }

  const moveTo = async (x: number, y: number) => {
    if (!playerId || !playerToken || !ui.selectedPieceId) return
    await commandApi.move(matchId, { player_id: playerId, player_token: playerToken, piece_id: ui.selectedPieceId, target_x: x, target_y: y })
    ui.setSelection(undefined, [])
  }

  const unlock = async (kind: string) => {
    if (!playerId || !playerToken) return
    await commandApi.unlock(matchId, { player_id: playerId, player_token: playerToken, kind })
  }

  const resign = async () => {
    if (!playerId || !playerToken) return
    await commandApi.resign(matchId, { player_id: playerId, player_token: playerToken })
  }

  return { selectPiece, moveTo, unlock, resign }
}
