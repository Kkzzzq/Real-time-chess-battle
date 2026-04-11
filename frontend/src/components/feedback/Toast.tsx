import type { NotificationItem } from '../../store/notificationStore'

type Props = { item: NotificationItem; onClose: (id: string) => void }

export function Toast({ item, onClose }: Props) {
  return (
    <div style={{ background: '#fff', border: '1px solid #d9d9d9', borderLeft: `4px solid ${item.level === 'error' ? '#cf1322' : item.level === 'warning' ? '#faad14' : '#1677ff'}`, padding: 8, minWidth: 220 }}>
      <div style={{ fontSize: 13 }}>{item.message}</div>
      <button onClick={() => onClose(item.id)} style={{ marginTop: 6 }}>关闭</button>
    </div>
  )
}
