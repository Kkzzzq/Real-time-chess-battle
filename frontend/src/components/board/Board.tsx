import type { MatchSnapshot } from '../../types/contracts'

type Props = { snapshot?: MatchSnapshot; selectedPieceId?: string; actionableTargets: [number, number][]; onCellClick: (x:number, y:number)=>void; onPieceClick: (pieceId:string)=>void }

export function Board({ snapshot, selectedPieceId, actionableTargets, onCellClick, onPieceClick }: Props) {
  const pieces = snapshot?.pieces.filter((p) => p.alive) || []
  const isTarget = (x:number,y:number) => actionableTargets.some(([tx,ty]) => tx===x && ty===y)
  return <div style={{display:'grid',gridTemplateColumns:'repeat(9,48px)',gap:2}}>{Array.from({length:10}).flatMap((_, y)=>Array.from({length:9}).map((__,x)=>{
    const piece = pieces.find((p)=>p.x===x&&p.y===y)
    return <button key={`${x}-${y}`} onClick={()=> piece ? onPieceClick(piece.id) : onCellClick(x,y)} style={{height:48,background:isTarget(x,y)?'#ffe58f':'#f5f5f5',border:selectedPieceId===piece?.id?'2px solid #1677ff':'1px solid #ccc'}}>{piece ? `${piece.owner===1?'红':'黑'}${piece.kind}` : ''}</button>
  }))}</div>
}
