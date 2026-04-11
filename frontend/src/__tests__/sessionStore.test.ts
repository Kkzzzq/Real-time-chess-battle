import { describe, it, expect } from 'vitest'
import { useSessionStore } from '../store/sessionStore'

describe('sessionStore', () => {
  it('persists and hydrates', () => {
    useSessionStore.getState().setSession({ playerId: 'p1', playerToken: 't1', matchId: 'm1' })
    useSessionStore.setState({ playerId: undefined, playerToken: undefined, matchId: undefined })
    useSessionStore.getState().hydrate()
    expect(useSessionStore.getState().playerId).toBe('p1')
    expect(useSessionStore.getState().playerToken).toBe('t1')
  })
})
