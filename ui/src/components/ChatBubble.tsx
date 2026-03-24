interface Props {
  role: 'user' | 'assistant'
  text: string
}

export default function ChatBubble({ role, text }: Props) {
  return (
    <div className={`chat-bubble chat-bubble--${role}`}>
      {text}
    </div>
  )
}
