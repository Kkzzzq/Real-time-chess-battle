import { create } from 'zustand'

interface RoomState {
  status?: string
  players: Record<string, { seat: number; name: string; ready: boolean; online: boolean; is_host: boolean; player_id?: string }>
  setPlayers: (players: RoomState['players']) => void
  setStatus: (status?: string) => void
}

export const useRoomStore = create<RoomState>((set) => ({
  players: {},
  setPlayers: (players) => set({ players }),
  setStatus: (status) => set({ status })
}))
