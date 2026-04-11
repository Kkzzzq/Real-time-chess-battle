import { useNotificationStore } from '../../store/notificationStore'
import { Toast } from './Toast'

export function NotificationCenter() {
  const { items, remove } = useNotificationStore()
  if (!items.length) return null
  return (
    <div style={{ position: 'fixed', right: 12, top: 12, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((item) => (
        <Toast key={item.id} item={item} onClose={remove} />
      ))}
    </div>
  )
}
