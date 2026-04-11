import { useState } from 'react'
import { LobbyPage } from './pages/LobbyPage'
import { RoomPage } from './pages/RoomPage'
import { GamePage } from './pages/GamePage'
import { useSessionStore } from './store/sessionStore'

export default function App(){
  const session = useSessionStore()
  const [page,setPage]=useState<'lobby'|'room'|'game'>('lobby')
  return <main style={{padding:16,fontFamily:'sans-serif'}}>
    {page==='lobby' && <LobbyPage onEnterMatch={(id)=>{session.setSession({matchId:id});setPage('room')}} />}
    {page==='room' && session.matchId && <RoomPage matchId={session.matchId} onStarted={()=>setPage('game')} />}
    {page==='game' && <GamePage />}
  </main>
}
