import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent, screen } from '@testing-library/react'
import { Board } from '../components/board/Board'

const snapshot: any = {
  runtime_board: { cells: Array.from({ length: 10 }, () => Array.from({ length: 9 }, () => ({ occupants: [], primary_occupant: null }))) },
  pieces: []
}
snapshot.runtime_board.cells[0][0] = { occupants: [{ piece_id: 'p1', owner: 1, kind: 'soldier', moving: false }], primary_occupant: { piece_id: 'p1', owner: 1, kind: 'soldier', moving: false } }


describe('Board', () => {
  it('renders grid cell', () => {
    render(<Board snapshot={undefined} selectedPieceId={undefined} actionableTargets={[]} onCellClick={() => {}} onPieceClick={() => {}} />)
    expect(screen.getAllByRole('button').length).toBe(90)
  })

  it('click occupied cell as move target when selectedPieceId exists', () => {
    const onCell = vi.fn()
    const onPiece = vi.fn()
    render(<Board snapshot={snapshot} selectedPieceId={'my_piece'} actionableTargets={[]} onCellClick={onCell} onPieceClick={onPiece} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    expect(onCell).toHaveBeenCalledWith(0, 0)
    expect(onPiece).not.toHaveBeenCalled()
  })
})
