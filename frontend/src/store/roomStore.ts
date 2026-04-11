import { create } from 'zustand'

type RoomPlayer = { seat: number; name: string; ready: boolean; online: boolean; is_host: boolean; player_id?: string }

interface RoomState {
  matchId?: string
  status?: string
  hostSeat?: number
  players: Record<string, RoomPlayer>
  loading: boolean
  reconnecting: boolean
  denied: boolean
  deleted: boolean
  roomError?: string
  setPlayers: (players: Record<string, RoomPlayer>) => void
  setStatus: (status?: string) => void
  setMatchId: (matchId?: string) => void
  setLoading: (loading: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setDenied: (denied: boolean) => void
  setDeleted: (deleted: boolean) => void
  setRoomError: (roomError?: string) => void
  clear: () => void
}

export const useRoomStore = create<RoomState>((set) => ({
  players: {},
  loading: false,
  reconnecting: false,
  denied: false,
  deleted: false,
  setPlayers: (players) => set({ players, hostSeat: Object.values(players).find((p) => p.is_host)?.seat }),
  setStatus: (status) => set({ status }),
  setMatchId: (matchId) => set({ matchId }),
  setLoading: (loading) => set({ loading }),
  setReconnecting: (reconnecting) => set({ reconnecting }),
  setDenied: (denied) => set({ denied }),
  setDeleted: (deleted) => set({ deleted }),
  setRoomError: (roomError) => set({ roomError }),
  clear: () => set({ matchId: undefined, status: undefined, hostSeat: undefined, players: {}, loading: false, reconnecting: false, denied: false, deleted: false, roomError: undefined })
}))
