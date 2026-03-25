import { useState, useEffect, useRef, useCallback } from 'react'
import { getIcebreaker, postTurn } from '../lib/api'
import type { ChatMessage, Speaker } from '../lib/types'
import MicButton from './MicButton'
import SpeakButton from './SpeakButton'
import Visualizer, { type VisualizerHandle } from './Visualizer'
import ChatBubble from './ChatBubble'

const CARTESIA_API_KEY = import.meta.env.VITE_CARTESIA_API_KEY as string
const SAMPLE_RATE = 44100

// ── Voice assignment ──────────────────────────────────────────────────────────
// VITE_CARTESIA_VOICES: comma-separated list of voice IDs to pick from randomly.
// Falls back to legacy single-voice env vars when the list is absent or too short.

const FALLBACK_VOICES: Record<Speaker, string> = {
  visitor:     import.meta.env.VITE_CARTESIA_VOICE_ID as string ?? '',
  consultant1: '6ccbfb76-1fc6-48f7-b71d-91ac6298247b', // Tessa
  consultant2: 'db69127a-dbaf-4fa9-b425-2fe67680c348', // Clint
}

function assignVoices(): Record<Speaker, string> {
  const pool = (import.meta.env.VITE_CARTESIA_VOICES as string ?? '')
    .split(',').map(v => v.trim()).filter(Boolean)
  if (pool.length < 3) return FALLBACK_VOICES
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  return { visitor: shuffled[0], consultant1: shuffled[1], consultant2: shuffled[2] }
}

function stripSsml(text: string): string {
  return text
    .replace(/<emotion[^>]*\/?>/gi, '')
    .replace(/<\/emotion>/gi, '')
    .replace(/\[laughter\]/gi, '')
    .replace(/\[clears throat\]/gi, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

const pause = (ms: number) => new Promise<void>(r => setTimeout(r, ms))

function formatText(text: string): string {
  return text.replace(/\bknowing\b/gi, '<em>knowing</em>')
}

export default function VoiceBox() {
  const [conversationId] = useState(() => {
    const stored = sessionStorage.getItem('t12n_conversation_id')
    if (stored) return stored
    const id = crypto.randomUUID()
    sessionStorage.setItem('t12n_conversation_id', id)
    return id
  })

  // Randomly assigned once per session, persisted across page reloads
  const [voiceIds] = useState<Record<Speaker, string>>(() => {
    const stored = sessionStorage.getItem('t12n_voices')
    if (stored) { try { return JSON.parse(stored) as Record<Speaker, string> } catch { /* fall through */ } }
    const voices = assignVoices()
    sessionStorage.setItem('t12n_voices', JSON.stringify(voices))
    return voices
  })

  const orderRef = useRef(0)

  type ConvState = 'idle' | 'visitor-speaking' | 'loading' | 'consultant-speaking' | 'waiting'
  const [convState,  setConvState]  = useState<ConvState>('idle')
  const [ttsState,   setTtsState]   = useState<'idle' | 'connecting' | 'playing'>('idle')
  const [messages,   setMessages]   = useState<ChatMessage[]>([])
  const [status,     setStatus]     = useState('')
  const [statusType, setStatusType] = useState<'' | 'error' | 'playing'>('')
  const [latencyMs,  setLatencyMs]  = useState<number | null>(null)

  const inputRef       = useRef<HTMLDivElement>(null)
  const audioCtxRef    = useRef<AudioContext | null>(null)
  const analyserRef    = useRef<AnalyserNode | null>(null)
  const vizRef         = useRef<VisualizerHandle>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const voiceboxBoxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getIcebreaker()
      .then(ib => { if (inputRef.current) inputRef.current.innerHTML = formatText(ib.text) })
      .catch(() => {
        if (inputRef.current && !inputRef.current.textContent?.trim())
          inputRef.current.innerHTML = formatText('The gap between knowing and doing is costing us.')
      })
  }, [])

  useEffect(() => {
    if (messages.length === 0) return
    requestAnimationFrame(() => {
      voiceboxBoxRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    })
  }, [messages])

  const getInputText = () => inputRef.current?.textContent?.trim() ?? ''

  const playPopSound = useCallback(() => {
    try {
      if (!audioCtxRef.current) audioCtxRef.current = new AudioContext()
      const ctx = audioCtxRef.current
      void ctx.resume()
      const osc  = ctx.createOscillator()
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

  const speakAs = useCallback((speaker: Speaker, text: string, overrideVoiceId?: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const voiceId = overrideVoiceId ?? voiceIds[speaker]
      const clean   = stripSsml(text)

      if (!CARTESIA_API_KEY || !voiceId) {
        setTtsState('playing'); setStatus('▶ Playing...'); setStatusType('playing')
        const ms = Math.max(800, clean.length * 45)
        setTimeout(() => { setTtsState('idle'); setStatus(''); setStatusType(''); resolve() }, ms)
        return
      }

      setTtsState('connecting'); setStatus('Connecting...'); setStatusType(''); setLatencyMs(null)
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

        let nextPlayTime = 0, firstChunk = true, settled = false

        const finish = () => {
          if (settled) return; settled = true
          ws.close(); vizRef.current?.stop()
          setTtsState('idle'); setStatus(''); setStatusType(''); resolve()
        }
        const fail = (msg: string) => {
          if (settled) return; settled = true
          ws.close(); vizRef.current?.stop()
          setTtsState('idle'); setStatus(msg); setStatusType('error'); reject(new Error(msg))
        }
        const scheduleChunk = (pcm: Float32Array) => {
          if (firstChunk) {
            setLatencyMs(Math.round(performance.now() - startMark))
            firstChunk = false; nextPlayTime = audioCtx.currentTime + 0.02
            setTtsState('playing'); setStatus('▶ Playing...'); setStatusType('playing')
            vizRef.current?.start(analyserRef.current!)
          }
          const buf = audioCtx.createBuffer(1, pcm.length, SAMPLE_RATE)
          buf.copyToChannel(pcm, 0)
          const src = audioCtx.createBufferSource()
          src.buffer = buf; src.connect(analyserRef.current!); src.start(nextPlayTime)
          nextPlayTime += buf.duration
        }

        ws.onopen = () => {
          setStatus('Synthesizing...')
          const payload: Record<string, unknown> = {
            context_id: crypto.randomUUID(), model_id: 'sonic-english', transcript: clean,
            voice: { mode: 'id', id: voiceId },
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
              const msg = JSON.parse(e.data as string) as { type?: string; data?: string }
              if (msg.type === 'error' || msg.type === 'done') {
                if (firstChunk) fail(`TTS error: ${(msg as Record<string,unknown>).error ?? JSON.stringify(msg)}`)
                else { const rem = Math.max(50, (nextPlayTime - audioCtx.currentTime) * 1000 + 150); setTimeout(finish, rem) }
                return
              }
              if (msg.data) {
                const bin = atob(msg.data); const bytes = new Uint8Array(bin.length)
                for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
                scheduleChunk(new Float32Array(bytes.buffer))
              }
            } catch (err) { console.error('WS msg error:', err) }
          }
        }
        ws.onerror = () => fail('Connection failed')
        ws.onclose = () => {
          if (firstChunk) { fail('No audio received'); return }
          const rem = Math.max(50, (nextPlayTime - audioCtx.currentTime) * 1000 + 150)
          setTimeout(finish, rem)
        }
      } catch (err) { setTtsState('idle'); reject(err) }
    })
  }, [voiceIds])

  const addBubble = useCallback((speaker: Speaker, text: string) => {
    setMessages(prev => [...prev, { id: crypto.randomUUID(), speaker, text }])
  }, [])

  const handleSubmit = useCallback(async (text: string) => {
    if (!text.trim()) return
    const visitorOrder = orderRef.current

    try {
      setConvState('visitor-speaking')
      await speakAs('visitor', text)

      playPopSound()
      addBubble('visitor', text)
      if (inputRef.current) inputRef.current.innerHTML = ''

      setConvState('loading')
      setStatus('Alex and Jamie are thinking...')
      setStatusType('')

      const [response] = await Promise.all([
        postTurn(conversationId, { order: visitorOrder, text, speaker: 'visitor', voices: voiceIds }),
        pause(2000),
      ])

      const replies = response.consultantReplies ?? []
      orderRef.current = visitorOrder + 1 + replies.length

      setStatus('')
      setConvState('consultant-speaking')

      for (let i = 0; i < replies.length; i++) {
        const reply = replies[i]
        if (i > 0) await pause(2000)
        playPopSound()
        addBubble(reply.speaker, reply.text)
        await speakAs(reply.speaker, reply.text, reply.voiceId)
      }

      setConvState('waiting')
      requestAnimationFrame(() => inputRef.current?.focus())

    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setStatusType('error')
      setConvState('waiting')
    }
  }, [conversationId, voiceIds, speakAs, playPopSound, addBubble])

  const handlePlay = useCallback(() => {
    const text = getInputText()
    if (text) void handleSubmit(text)
  }, [handleSubmit])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handlePlay() }
  }

  const isBusy = convState !== 'idle' && convState !== 'waiting'

  return (
    <div className="voicebox">
      {messages.length > 0 && (
        <div className="chat-area">
          {messages.map(msg => (
            <ChatBubble key={msg.id} speaker={msg.speaker} text={msg.text} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div ref={voiceboxBoxRef} className="voicebox-box">
        <div className="voicebox-input-area">
          <div
            ref={inputRef}
            contentEditable
            suppressContentEditableWarning
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
              onTranscript={t => { if (inputRef.current) inputRef.current.textContent = t }}
              onEnd={handlePlay}
              onError={msg => { setStatus(msg); setStatusType('error') }}
              disabled={isBusy}
            />
            <SpeakButton state={ttsState} onClick={handlePlay} disabled={isBusy} />
          </div>
        </div>
      </div>

      <Visualizer ref={vizRef} />

      {status && (
        <div className="voicebox-status" style={{
          color: statusType === 'error'   ? '#ff6b6b'
               : statusType === 'playing' ? 'var(--accent)'
               : 'rgba(245,240,232,0.4)',
        }}>
          {status}
        </div>
      )}
    </div>
  )
}
