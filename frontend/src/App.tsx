import { Navigate, Route, Routes } from 'react-router-dom'
import { NotificationCenter } from './components/feedback/NotificationCenter'
import { GamePage } from './pages/GamePage'
import { LobbyPage } from './pages/LobbyPage'
import { RoomPage } from './pages/RoomPage'

export default function App() {
  return (
    <main style={{ padding: 16, fontFamily: 'sans-serif' }}>
      <NotificationCenter />
      <Routes>
        <Route path='/' element={<LobbyPage />} />
        <Route path='/room/:matchId' element={<RoomPage />} />
        <Route path='/game/:matchId' element={<GamePage />} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </main>
  )
}
