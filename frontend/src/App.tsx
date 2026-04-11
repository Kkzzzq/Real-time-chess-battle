import { Navigate, Route, Routes } from 'react-router-dom'
import { LobbyPage } from './pages/LobbyPage'
import { RoomPage } from './pages/RoomPage'
import { GamePage } from './pages/GamePage'

export default function App() {
  return (
    <main style={{ padding: 16, fontFamily: 'sans-serif' }}>
      <Routes>
        <Route path='/' element={<LobbyPage />} />
        <Route path='/room/:matchId' element={<RoomPage />} />
        <Route path='/game/:matchId' element={<GamePage />} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </main>
  )
}
