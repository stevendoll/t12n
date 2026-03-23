interface Props {
  state: 'idle' | 'connecting' | 'playing'
  disabled?: boolean
  onClick: () => void
}

export default function SpeakButton({ state, disabled, onClick }: Props) {
  const label = state === 'idle' ? 'Play' : state === 'connecting' ? '...' : 'Playing'

  return (
    <button
      onClick={onClick}
      disabled={disabled || state !== 'idle'}
      className="bg-[#FFFF33] text-[var(--black)] border-none font-mono text-[0.72rem] font-medium tracking-[0.12em] uppercase px-7 py-3 rounded-sm cursor-none transition-all flex items-center gap-2 hover:bg-[#FFFF66] hover:-translate-y-px disabled:opacity-50 disabled:translate-y-0"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <path d="M8 5v14l11-7z" />
      </svg>
      {label}
    </button>
  )
}
