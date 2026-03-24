import { useState, useEffect, useRef, useCallback } from 'react'
import { getIcebreaker } from '../lib/api'
import MicButton from './MicButton'
import SpeakButton from './SpeakButton'
import Visualizer, { type VisualizerHandle } from './Visualizer'
import ChatBubble from './ChatBubble'

const CARTESIA_API_KEY = import.meta.env.VITE_CARTESIA_API_KEY as string
const VOICE_ID = import.meta.env.VITE_CARTESIA_VOICE_ID as string
const SAMPLE_RATE = 44100

type ChatMsg = { id: number; role: 'user' | 'assistant'; text: string }

const pause = (ms: number) => new Promise<void>(r => setTimeout(r, ms))

// Mock: simulates a 2-turn AI consultant response (fast — pacing is handled by the caller)
function mockConversationTurns(_userText: string): Promise<[string, string]> {
  return new Promise(resolve =>
    setTimeout(() => resolve([
      "That friction you're describing — knowing AI matters but not knowing what to actually do — is exactly where most organizations get stuck. The gap isn't ambition, it's execution architecture.",
      "The organizations that move fastest start with a focused 90-day sprint: identify the highest-leverage use case, build proof of value, and create internal momentum. What does your current AI initiative look like — do you have a clear first target, or are you still mapping the landscape?",
    ]), 400)
  )
}

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
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [conversing, setConversing] = useState(false)

  const inputRef = useRef<HTMLDivElement>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const vizRef = useRef<VisualizerHandle>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  // Scroll to latest bubble after each render with new messages
  useEffect(() => {
    const el = messagesEndRef.current
    if (!el) return
    // rAF ensures the new bubble is in the DOM before we scroll
    requestAnimationFrame(() => {
      el.scrollIntoView({ behavior: 'smooth', block: 'end' })
    })
  }, [messages])

  const formatText = (text: string): string => {
    return text.replace(/\bknowing\b/gi, '<em>knowing</em>')
  }

  const getInputText = () => inputRef.current?.textContent?.trim() ?? ''

  // Short soft chime using the Web Audio API oscillator
  const playPopSound = useCallback(() => {
    try {
      if (!audioCtxRef.current) audioCtxRef.current = new AudioContext()
      const ctx = audioCtxRef.current
      void ctx.resume()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.setValueAtTime(920, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(520, ctx.currentTime + 0.09)
      gain.gain.setValueAtTime(0.07, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.14)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + 0.14)
    } catch { /* ignore */ }
  }, [])

  // Speaks text via Cartesia WebSocket, returns a Promise that resolves when audio finishes
  const speakText = useCallback((text: string): Promise<void> => {
    return new Promise((resolve, reject) => {

      // No TTS configured — simulate with a timed delay so the flow still works locally
      if (!CARTESIA_API_KEY || !VOICE_ID) {
        setTtsState('playing')
        setStatus('▶ Playing...')
        setStatusType('playing')
        const ms = Math.max(800, text.length * 45)
        setTimeout(() => {
          setTtsState('idle')
          setStatus('')
          setStatusType('')
          resolve()
        }, ms)
        return
      }

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
        let settled = false

        // Called exactly once — cleans up and resolves the outer Promise
        const finish = () => {
          if (settled) return
          settled = true
          ws.close()
          vizRef.current?.stop()
          setTtsState('idle')
          setStatus('')
          setStatusType('')
          resolve()
        }

        const fail = (msg: string) => {
          if (settled) return
          settled = true
          ws.close()
          vizRef.current?.stop()
          setTtsState('idle')
          setStatus(msg)
          setStatusType('error')
          reject(new Error(msg))
        }

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
          const payload: Record<string, unknown> = {
            context_id: crypto.randomUUID(),
            model_id: 'sonic-english',
            transcript: text,
            voice: { mode: 'id', id: VOICE_ID },
            output_format: { container: 'raw', encoding: 'pcm_f32le', sample_rate: SAMPLE_RATE },
          }
          payload['continue'] = false
          ws.send(JSON.stringify(payload))
        }

        ws.onmessage = (e) => {
          if (e.data instanceof ArrayBuffer) {
            scheduleChunk(new Float32Array(e.data))
          } else {
            try {
              const msg = JSON.parse(e.data as string) as { type?: string; data?: string; status_code?: number }
              // Cartesia sends {"type":"error","done":true} as its stream-end signal
              // after delivering all audio. Only treat it as fatal if no audio arrived yet.
              if (msg.type === 'error' || msg.type === 'done') {
                if (firstChunk) {
                  fail(`TTS error: ${(msg as Record<string,unknown>).error as string ?? JSON.stringify(msg)}`)
                } else {
                  const now = audioCtx.currentTime
                  const remaining = Math.max(50, (nextPlayTime - now) * 1000 + 150)
                  setTimeout(finish, remaining)
                }
                return
              }
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

        ws.onerror = () => { fail('Connection failed') }

        ws.onclose = () => {
          if (firstChunk) { fail('No audio received'); return }
          // Fallback: WS closed without a "done" message — wait for remaining audio
          const now = audioCtx.currentTime
          const remaining = Math.max(50, (nextPlayTime - now) * 1000 + 150)
          setTimeout(finish, remaining)
        }
      } catch (err) {
        vizRef.current?.stop()
        setTtsState('idle')
        setStatus(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
        setStatusType('error')
        reject(err)
      }
    })
  }, [])

  // Full conversation flow: speak input → user bubble → mock API → 2 assistant bubbles
  const handlePlay = useCallback(async () => {
    const text = getInputText()
    if (!text || ttsState !== 'idle' || conversing) return

    setConversing(true)
    setStatus('')
    setStatusType('')

    try {
      // 1. Speak the user's typed/spoken text
      await speakText(text)

      // 2. Sound + user bubble left + clear input
      playPopSound()
      setMessages(prev => [...prev, { id: Date.now(), role: 'user', text }])
      if (inputRef.current) inputRef.current.innerHTML = ''

      // 3. Fetch mock turns while pausing 2s before showing the first reply
      const [turn1, turn2] = await Promise.all([mockConversationTurns(text), pause(2000)])

      // 4. Sound + first assistant bubble right + speak it
      playPopSound()
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: turn1 }])
      await speakText(turn1)

      // 5. 2s pause, then sound + second assistant bubble right + speak it
      await pause(2000)
      playPopSound()
      setMessages(prev => [...prev, { id: Date.now() + 2, role: 'assistant', text: turn2 }])
      await speakText(turn2)

    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setStatusType('error')
    } finally {
      setConversing(false)
    }
  }, [ttsState, conversing, speakText, playPopSound])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handlePlay()
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
      {messages.length > 0 && (
        <div className="chat-area">
          {messages.map(msg => (
            <ChatBubble key={msg.id} role={msg.role} text={msg.text} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
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
              onEnd={() => void handlePlay()}
              onError={handleMicError}
              disabled={ttsState !== 'idle' || conversing}
            />
            <SpeakButton
              state={ttsState}
              onClick={() => void handlePlay()}
              disabled={conversing}
            />
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
