import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { useSessionStore } from './store/sessionStore'

useSessionStore.getState().hydrate()
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
