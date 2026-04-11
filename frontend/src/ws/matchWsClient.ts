import { useWsStore } from '../store/wsStore'
import { useMatchStore } from '../store/matchStore'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000'

/**
 * WS auth strategy:
 * - player_token is validated at connection handshake via query string.
 * - command frames then carry player_id only (backend binds frame player_id to connection player_id).
 */
export class MatchWsClient {
  private ws?: WebSocket
  private heartbeat?: number
  private reconnectTimer?: number

  connect(matchId: string, playerId?: string, playerToken?: string) {
    const qp = playerId && playerToken ? `?player_id=${playerId}&player_token=${playerToken}` : ''
    this.ws = new WebSocket(`${WS_BASE}/matches/${matchId}/ws${qp}`)
    useWsStore.getState().setState({ reconnecting: false })

    this.ws.onopen = () => {
      useWsStore.getState().setState({ connected: true, error: undefined })
      this.heartbeat = window.setInterval(() => this.sendPing(), 10000)
    }
    this.ws.onclose = () => {
      useWsStore.getState().setState({ connected: false, reconnecting: true })
      if (this.heartbeat) window.clearInterval(this.heartbeat)
      this.reconnectTimer = window.setTimeout(() => this.connect(matchId, playerId, playerToken), 2000)
    }
    this.ws.onerror = () => useWsStore.getState().setState({ error: 'ws error' })
    this.ws.onmessage = (evt) => {
      useWsStore.getState().setState({ lastMessageTs: Date.now() })
      const frame = JSON.parse(evt.data) as { type: string; data: any }
      switch (frame.type) {
        case 'subscribed':
          useMatchStore.getState().setSubscribedMeta(frame.data)
          break
        case 'snapshot':
          useMatchStore.getState().setSnapshot(frame.data)
          break
        case 'event':
          useMatchStore.getState().pushEvents([frame.data])
          break
        case 'events':
          useMatchStore.getState().pushEvents(frame.data?.events || [])
          break
        case 'command_result':
          useMatchStore.getState().setCommandResult(frame.data)
          break
        case 'pong':
          break
        case 'error':
          useWsStore.getState().setState({ error: frame.data?.message || 'ws error' })
          break
        default:
          break
      }
    }
  }
  disconnect() { if (this.reconnectTimer) clearTimeout(this.reconnectTimer); if (this.heartbeat) clearInterval(this.heartbeat); this.ws?.close() }
  sendMove(player_id: string, piece_id: string, target_x: number, target_y: number) { this.ws?.send(JSON.stringify({ type: 'move', player_id, piece_id, target_x, target_y })) }
  sendUnlock(player_id: string, kind: string) { this.ws?.send(JSON.stringify({ type: 'unlock', player_id, kind })) }
  sendResign(player_id: string) { this.ws?.send(JSON.stringify({ type: 'resign', player_id })) }
  sendPing() { this.ws?.send(JSON.stringify({ type: 'ping' })) }
}

export const wsClient = new MatchWsClient()
