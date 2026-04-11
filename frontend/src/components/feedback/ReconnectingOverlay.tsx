type Props = { open: boolean }
export function ReconnectingOverlay({ open }: Props) {
  if (!open) return null
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
      <div style={{ background: '#fff', padding: 16, borderRadius: 8 }}>正在重连...</div>
    </div>
  )
}
