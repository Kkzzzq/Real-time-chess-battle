type Props = { text: string }
export function ErrorState({ text }: Props) {
  return <div style={{ padding: 8, color: '#cf1322' }}>{text}</div>
}
