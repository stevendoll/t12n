import { useState, useRef } from 'react'

interface Props {
  onTranscript: (text: string) => void
  onError: (msg: string) => void
  disabled?: boolean
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnySpeechRecognition = any

export default function MicButton({ onTranscript, onError, disabled }: Props) {
  const [recording, setRecording] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const SR: AnySpeechRecognition = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition
  if (!SR) return null

  const toggle = () => {
    if (recording) {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-call
      recognitionRef.current?.stop()
      return
    }

    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    const rec = new SR()
    rec.continuous = false
    rec.interimResults = true
    rec.lang = 'en-US'
    recognitionRef.current = rec

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rec.onresult = (e: any) => {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
      const transcript = Array.from(e.results as ArrayLike<SpeechRecognitionResult>)
        .map(r => r[0].transcript).join('')
      onTranscript(transcript)
    }
    rec.onend = () => setRecording(false)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rec.onerror = (e: any) => {
      setRecording(false)
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      onError(`Mic error: ${e.error}`)
    }

    setRecording(true)
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    rec.start()
  }

  return (
    <button
      onClick={toggle}
      disabled={disabled}
      title={recording ? 'Listening… click to stop' : 'Speak your concern'}
      className={[
        'border-none px-4 flex items-start pt-6 flex-shrink-0 rounded-tr-sm rounded-br-sm transition-all cursor-none',
        recording
          ? 'bg-[#ff6b6b] border-l border-[#ff6b6b] text-white animate-[micPulse_1s_ease-in-out_infinite]'
          : 'bg-[var(--accent)] border-l border-[var(--accent)] text-[var(--black)] hover:bg-[var(--accent-bright)] hover:border-[var(--accent-bright)]',
      ].join(' ')}
    >
      <svg className="w-[18px] h-[18px] fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm0 2a2 2 0 0 0-2 2v6a2 2 0 0 0 4 0V5a2 2 0 0 0-2-2zm7 8a1 1 0 0 1 1 1 8 8 0 0 1-7 7.938V21h2a1 1 0 0 1 0 2H9a1 1 0 0 1 0-2h2v-1.062A8 8 0 0 1 4 12a1 1 0 0 1 2 0 6 6 0 0 0 12 0 1 1 0 0 1 1-1z" />
      </svg>
    </button>
  )
}
