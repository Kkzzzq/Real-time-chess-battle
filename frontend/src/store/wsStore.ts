import { create } from 'zustand'

interface WsState { connected: boolean; reconnecting: boolean; lastMessageTs?: number; error?: string; setState: (patch: Partial<WsState>) => void }
export const useWsStore = create<WsState>((set) => ({ connected: false, reconnecting: false, setState: (patch) => set((s) => ({ ...s, ...patch })) }))
