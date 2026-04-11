import { useEffect } from 'react'
import { wsClient } from '../ws/matchWsClient'

export function useMatchRealtime(matchId?: string, playerId?: string, playerToken?: string) {
  useEffect(() => {
    if (!matchId || !playerId || !playerToken) return
    wsClient.connect(matchId, playerId, playerToken)
    return () => wsClient.disconnect()
  }, [matchId, playerId, playerToken])
}
