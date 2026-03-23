import { useState, useEffect, useRef, useCallback } from 'react'
import { getIcebreaker } from '../lib/api'
import MicButton from './MicButton'
import SpeakButton from './SpeakButton'
import Visualizer, { type VisualizerHandle } from './Visualizer'

const CARTESIA_API_KEY = import.meta.env.VITE_CARTESIA_API_KEY as string
const VOICE_ID = import.meta.env.VITE_CARTESIA_VOICE_ID as string
const SAMPLE_RATE = 44100
const AUTO_PLAY_DELAY_MS = 15_000

export default function VoiceBox() {
  const [conversationId] = useState(() => {
    const stored = sessionStorage.getItem('t12n_conversation_id')
    if (stored) return stored
    const id = crypto.randomUUID()
    sessionStorage.setItem('t12n_conversation_id', id)
    return id
  })

  const [, setNextOrder] = useState(0)
  const [ttsState, setTtsState] = useState<'idle' | 'connecting' | 'playing'>('idle')
  const [status, setStatus] = useState('')
  const [statusType, setStatusType] = useState<'' | 'error' | 'playing'>('')
  const [latencyMs, setLatencyMs] = useState<number | null>(null)

  const inputRef = useRef<HTMLDivElement>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const vizRef = useRef<VisualizerHandle>(null)
  const autoPlayTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load icebreaker on mount
  useEffect(() => {
    getIcebreaker()
      .then(async (icebreaker) => {
        if (inputRef.current) {
          inputRef.current.innerHTML = formatText(icebreaker.text)
        }

        setNextOrder(1)

        // Auto-play after 15 seconds
        autoPlayTimerRef.current = setTimeout(() => {
          speak(icebreaker.text)
        }, AUTO_PLAY_DELAY_MS)
      })
      .catch(() => {
        // API not available — use default text
        if (inputRef.current && !inputRef.current.textContent?.trim()) {
          inputRef.current.innerHTML = formatText('The gap between knowing and doing is costing us.')
        }
      })

    return () => {
      if (autoPlayTimerRef.current) clearTimeout(autoPlayTimerRef.current)
    }
  }, [conversationId])

  const formatText = (text: string): string => {
    // Wrap "knowing" in em for styling
    return text.replace(/\bknowing\b/gi, '<em>knowing</em>')
  }

  const getInputText = () => inputRef.current?.textContent?.trim() ?? ''

  const speak = useCallback(async (textOverride?: string) => {
    const text = textOverride ?? getInputText()
    if (!text) return

    if (autoPlayTimerRef.current) {
      clearTimeout(autoPlayTimerRef.current)
      autoPlayTimerRef.current = null
    }

    setTtsState('connecting')
    setStatus('Connecting...')
    setStatusType('')
    setLatencyMs(null)

    const startMark = performance.now()

    try {
      if (!audioCtxRef.current) audioCtxRef.current = new AudioContext()
      // Fire resume without awaiting — browser may block it until a user gesture,
      // and awaiting a blocked promise would hang the entire speak() call.
      void audioCtxRef.current.resume()
      const audioCtx = audioCtxRef.current

      analyserRef.current = audioCtx.createAnalyser()
      analyserRef.current.fftSize = 256
      analyserRef.current.connect(audioCtx.destination)

      const wsUrl = `wss://api.cartesia.ai/tts/websocket?api_key=${CARTESIA_API_KEY}&cartesia_version=2024-06-10`
      const ws = new WebSocket(wsUrl)
      ws.binaryType = 'arraybuffer'

      let nextPlayTime = 0
      let firstChunk = true

      const scheduleChunk = (pcm: Float32Array) => {
        if (firstChunk) {
          const ms = Math.round(performance.now() - startMark)
          setLatencyMs(ms)
          firstChunk = false
          nextPlayTime = audioCtx.currentTime + 0.02
          setTtsState('playing')
          setStatus('▶ Playing...')
          setStatusType('playing')
          vizRef.current?.start(analyserRef.current!)
        }
        const buf = audioCtx.createBuffer(1, pcm.length, SAMPLE_RATE)
        buf.copyToChannel(pcm, 0)
        const src = audioCtx.createBufferSource()
        src.buffer = buf
        src.connect(analyserRef.current!)
        src.start(nextPlayTime)
        nextPlayTime += buf.duration
      }

      ws.onopen = () => {
        setStatus('Synthesizing...')
        ws.send(JSON.stringify({
          context_id: crypto.randomUUID(),
          model_id: 'sonic-english',
          transcript: text,
          voice: { mode: 'id', id: VOICE_ID },
          output_format: { container: 'raw', encoding: 'pcm_f32le', sample_rate: SAMPLE_RATE },
          continue: false,
        }))
      }

      ws.onmessage = (e) => {
        if (e.data instanceof ArrayBuffer) {
          scheduleChunk(new Float32Array(e.data))
        } else {
          try {
            const msg = JSON.parse(e.data as string) as { type?: string; data?: string }
            if (msg.type === 'error') throw new Error(JSON.stringify(msg))
            if (msg.data) {
              const bin = atob(msg.data)
              const bytes = new Uint8Array(bin.length)
              for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
              scheduleChunk(new Float32Array(bytes.buffer))
            }
          } catch (err) {
            console.error('WS msg error:', err)
          }
        }
      }

      ws.onerror = () => {
        vizRef.current?.stop()
        setTtsState('idle')
        setStatus('WebSocket connection failed')
        setStatusType('error')
      }

      ws.onclose = () => {
        if (firstChunk) {
          vizRef.current?.stop()
          setTtsState('idle')
          setStatus('No audio received')
          setStatusType('error')
          return
        }
        // If AudioContext is still suspended (no user gesture), don't poll forever
        if (audioCtx.state === 'suspended') {
          vizRef.current?.stop()
          setTtsState('idle')
          setStatus('')
          setStatusType('')
          return
        }
        const poll = () => {
          if (audioCtx.currentTime < nextPlayTime) {
            setTimeout(poll, 100)
          } else {
            vizRef.current?.stop()
            setTtsState('idle')
            setStatus('')
            setStatusType('')
          }
        }
        poll()
      }
    } catch (err) {
      vizRef.current?.stop()
      setTtsState('idle')
      setStatus(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setStatusType('error')
    }
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void speak()
    }
  }

  const handleMicTranscript = (text: string) => {
    if (inputRef.current) inputRef.current.textContent = text
  }

  const handleMicError = (msg: string) => {
    setStatus(msg)
    setStatusType('error')
  }

  return (
    <div className="w-full max-w-[900px] opacity-0 animate-[fadeUp_1s_0.35s_forwards]">
      <div className="border border-[var(--border)] bg-[rgba(245,240,232,0.03)] backdrop-blur-sm rounded-sm p-1 transition-colors focus-within:border-[rgba(77,182,172,0.4)]">
        <div className="flex items-start gap-0">
          <div
            ref={inputRef}
            contentEditable
            suppressContentEditableWarning
            data-placeholder="The gap between knowing and doing is costing us."
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent border-none outline-none text-[var(--accent)] font-serif text-[clamp(2.5rem,6vw,5rem)] italic font-normal leading-[1.1] tracking-[-0.02em] px-7 py-6 min-h-[120px] text-center cursor-text [&_em]:text-[var(--white)] [&_em]:italic empty:before:content-[attr(data-placeholder)] empty:before:text-[rgba(245,240,232,0.3)] empty:before:italic"
          />
          <MicButton
            onTranscript={handleMicTranscript}
            onEnd={() => void speak()}
            onError={handleMicError}
            disabled={ttsState !== 'idle'}
          />
        </div>
        <div className="flex justify-between items-center px-4 py-[10px] pl-7 border-t border-[var(--border)]">
          <span className="text-[0.65rem] tracking-[0.1em] uppercase text-[rgba(245,240,232,0.25)]">
            ↵ enter to hear it back
            {latencyMs !== null && (
              <span className="inline-block text-[0.6rem] tracking-[0.12em] uppercase text-[rgba(77,182,172,0.5)] bg-[rgba(77,182,172,0.06)] border border-[rgba(77,182,172,0.15)] px-2 py-[3px] rounded-sm ml-2 align-middle">
                {latencyMs}ms
              </span>
            )}
          </span>
          <SpeakButton state={ttsState} onClick={() => void speak()} />
        </div>
      </div>
      <Visualizer ref={vizRef} />
      {status && (
        <div className={[
          'text-[0.68rem] tracking-[0.1em] text-center mt-[14px] min-h-5 transition-all',
          statusType === 'error' ? 'text-[#ff6b6b]' : statusType === 'playing' ? 'text-[var(--accent)]' : 'text-[rgba(245,240,232,0.3)]',
        ].join(' ')}>
          {status}
        </div>
      )}
    </div>
  )
}
