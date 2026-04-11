type Props = { text?: string }
export function LoadingState({ text = '加载中...' }: Props) {
  return <div style={{ padding: 8, color: '#595959' }}>{text}</div>
}
