import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Board } from '../components/board/Board'

describe('Board', () => {
  it('renders grid cell', () => {
    render(<Board snapshot={undefined} selectedPieceId={undefined} actionableTargets={[]} onCellClick={() => {}} onPieceClick={() => {}} />)
    expect(screen.getAllByRole('button').length).toBe(90)
  })
})
