import { useState, useEffect, useRef, useCallback } from 'react'
import { getIcebreaker } from '../lib/api'
import MicButton from './MicButton'
import SpeakButton from './SpeakButton'
import Visualizer, { type VisualizerHandle } from './Visualizer'

const CARTESIA_API_KEY = import.meta.env.VITE_CARTESIA_API_KEY as string
const VOICE_ID = import.meta.env.VITE_CARTESIA_VOICE_ID as string
const SAMPLE_RATE = 44100

export default function VoiceBox() {
  const [conversationId] = useState(() => {
    const stored = sessionStorage.getItem('t12n_conversation_id')
    if (stored) return stored
    const id = crypto.randomUUID()
    sessionStorage.setItem('t12n_conversation_id', id)
    return id
  })

  const [ttsState, setTtsState] = useState<'idle' | 'connecting' | 'playing'>('idle')
  const [status, setStatus] = useState('')
  const [statusType, setStatusType] = useState<'' | 'error' | 'playing'>('')
  const [latencyMs, setLatencyMs] = useState<number | null>(null)

  const inputRef = useRef<HTMLDivElement>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const vizRef = useRef<VisualizerHandle>(null)

  useEffect(() => {
    getIcebreaker()
      .then((icebreaker) => {
        if (inputRef.current) {
          inputRef.current.innerHTML = formatText(icebreaker.text)
        }
      })
      .catch(() => {
        if (inputRef.current && !inputRef.current.textContent?.trim()) {
          inputRef.current.innerHTML = formatText('The gap between knowing and doing is costing us.')
        }
      })
  }, [conversationId])

  const formatText = (text: string): string => {
    return text.replace(/\bknowing\b/gi, '<em>knowing</em>')
  }

  const getInputText = () => inputRef.current?.textContent?.trim() ?? ''

  const speak = useCallback(async (textOverride?: string) => {
    const text = textOverride ?? getInputText()
    if (!text) return

    setTtsState('connecting')
    setStatus('Connecting...')
    setStatusType('')
    setLatencyMs(null)

    const startMark = performance.now()

    try {
      if (!audioCtxRef.current) audioCtxRef.current = new AudioContext()
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
    <div className="voicebox">
      <div className="voicebox-box">
        <div className="voicebox-input-area">
          <div
            ref={inputRef}
            contentEditable
            suppressContentEditableWarning
            data-placeholder="The gap between knowing and doing is costing us."
            onKeyDown={handleKeyDown}
            className="voicebox-input"
          />
        </div>
        <div className="voicebox-toolbar">
          <span className="voicebox-hint">
            ↵ enter and let's talk
            {latencyMs !== null && <span className="voicebox-latency">{latencyMs}ms</span>}
          </span>
          <div className="voicebox-toolbar-right">
            <MicButton
              onTranscript={handleMicTranscript}
              onEnd={() => void speak()}
              onError={handleMicError}
              disabled={ttsState !== 'idle'}
            />
            <SpeakButton state={ttsState} onClick={() => void speak()} />
          </div>
        </div>
      </div>
      <Visualizer ref={vizRef} />
      {status && (
        <div
          className="voicebox-status"
          style={{ color: statusType === 'error' ? '#ff6b6b' : statusType === 'playing' ? 'var(--accent)' : 'rgba(245,240,232,0.3)' }}
        >
          {status}
        </div>
      )}
    </div>
  )
}
