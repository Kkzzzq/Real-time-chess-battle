import { create } from 'zustand'

type RoomPlayer = { seat: number; name: string; ready: boolean; online: boolean; is_host: boolean; player_id?: string }

interface RoomState {
  matchId?: string
  status?: string
  hostSeat?: number
  players: Record<string, RoomPlayer>
  loading: boolean
  reconnecting: boolean
  roomError?: string
  setPlayers: (players: Record<string, RoomPlayer>) => void
  setStatus: (status?: string) => void
  setMatchId: (matchId?: string) => void
  setLoading: (loading: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setRoomError: (roomError?: string) => void
  clear: () => void
}

export const useRoomStore = create<RoomState>((set) => ({
  players: {},
  loading: false,
  reconnecting: false,
  setPlayers: (players) => set({ players, hostSeat: Object.values(players).find((p) => p.is_host)?.seat }),
  setStatus: (status) => set({ status }),
  setMatchId: (matchId) => set({ matchId }),
  setLoading: (loading) => set({ loading }),
  setReconnecting: (reconnecting) => set({ reconnecting }),
  setRoomError: (roomError) => set({ roomError }),
  clear: () => set({ matchId: undefined, status: undefined, hostSeat: undefined, players: {}, loading: false, reconnecting: false, roomError: undefined })
}))
