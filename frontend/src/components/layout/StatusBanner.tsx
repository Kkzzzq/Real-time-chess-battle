export function StatusBanner({ loading, error, notice, onRetry }: { loading?: boolean; error?: string; notice?: string; onRetry?: () => void }) {
  if (loading) return <div style={{ padding: 8, background: '#e6f4ff' }}>加载中...</div>
  if (error) return <div style={{ padding: 8, background: '#fff1f0' }}>错误: {error} {onRetry ? <button onClick={onRetry}>重试</button> : null}</div>
  if (notice) return <div style={{ padding: 8, background: '#fffbe6' }}>{notice}</div>
  return null
}
