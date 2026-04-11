import { describe, it, expect } from 'vitest'
import { useMatchStore } from '../store/matchStore'

describe('matchStore', () => {
  it('merges snapshot events and ws events without dropping', () => {
    useMatchStore.setState({ recentEvents: [] } as any)
    useMatchStore.getState().setSnapshot({ events: [{ type: 'a', ts_ms: 1, payload: {} }] } as any)
    useMatchStore.getState().pushEvents([{ type: 'b', ts_ms: 2, payload: {} }])
    useMatchStore.getState().setSnapshot({ events: [{ type: 'a', ts_ms: 1, payload: {} }] } as any)
    expect(useMatchStore.getState().recentEvents.map((e) => e.type)).toEqual(['a', 'b'])
  })
})
