import { useWsStore } from '../../store/wsStore'
export function ConnectionStatus(){ const ws=useWsStore(); return <div>WS: {ws.connected?'connected':ws.reconnecting?'reconnecting':'disconnected'} {ws.error?`(${ws.error})`:''}</div> }
