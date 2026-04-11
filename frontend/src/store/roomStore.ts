import { create } from 'zustand'

interface RoomState { players: Record<string, { name: string; ready: boolean; online: boolean; is_host: boolean }>; setPlayers: (players: RoomState['players']) => void }
export const useRoomStore = create<RoomState>((set) => ({ players: {}, setPlayers: (players) => set({ players }) }))
