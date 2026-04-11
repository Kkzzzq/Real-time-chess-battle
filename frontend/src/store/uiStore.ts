import { create } from 'zustand'

interface UiState {
  selectedPieceId?: string
  actionableTargets: [number, number][]
  unlockOpen: boolean
  error?: string
  notice?: string
  setSelection: (pieceId?: string, targets?: [number, number][]) => void
  setUnlockOpen: (open: boolean) => void
  setError: (error?: string) => void
  setNotice: (notice?: string) => void
}

export const useUiStore = create<UiState>((set) => ({
  actionableTargets: [],
  unlockOpen: false,
  setSelection: (pieceId, targets = []) => set({ selectedPieceId: pieceId, actionableTargets: targets }),
  setUnlockOpen: (open) => set({ unlockOpen: open }),
  setError: (error) => set({ error }),
  setNotice: (notice) => set({ notice })
}))
