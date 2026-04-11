import { create } from 'zustand'
import type { MatchSnapshot } from '../types/contracts'

interface MatchState { snapshot?: MatchSnapshot; setSnapshot: (snapshot: MatchSnapshot) => void }
export const useMatchStore = create<MatchState>((set) => ({ setSnapshot: (snapshot) => set({ snapshot }) }))
