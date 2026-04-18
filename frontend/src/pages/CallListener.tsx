import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Room, RoomEvent, type TranscriptionSegment } from 'livekit-client'
import Layout from '../components/Layout'
import { ArrowLeft, Mic, AlertTriangle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type Status = 'fetching_token' | 'connecting' | 'live' | 'error' | 'ended'

export default function CallListener() {
  const { callId } = useParams<{ callId: string }>()
  const navigate = useNavigate()
  const { token } = useAuth()

  const [status, setStatus] = useState<Status>('fetching_token')
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [lines, setLines] = useState<{ who: string; text: string; at: number }[]>([])
  const [duration, setDuration] = useState(0)

  const roomRef = useRef<Room | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  useEffect(() => {
    const t = setInterval(() => setDuration(d => d + 1), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!callId) {
      setStatus('error')
      setErrorMsg('No call id in URL')
      return
    }

    let cleaned = false

    const join = async () => {
      if (!token) {
        setStatus('error')
        setErrorMsg('Not signed in — please sign in first.')
        return
      }

      // 1. Fetch listener token (authed via Bearer token from AuthContext)
      const headers: HeadersInit = { Authorization: `Bearer ${token}` }

      let resp: Response
      try {
        resp = await fetch(`${API_URL}/calls/${callId}/listener-token`, { headers })
      } catch (e) {
        if (!cleaned) { setStatus('error'); setErrorMsg('Network error reaching backend') }
        return
      }
      if (!resp.ok) {
        if (!cleaned) {
          setStatus('error')
          setErrorMsg(
            resp.status === 400
              ? 'Call has no active room yet (agent may not have joined, or call ended).'
              : resp.status === 401
              ? 'Not authenticated — please sign in again.'
              : resp.status === 404
              ? 'Call not found.'
              : `Backend returned ${resp.status}`,
          )
        }
        return
      }
      const { token: lkToken, room_name, livekit_url } = await resp.json()

      if (cleaned) return

      // 2. Create LiveKit room and subscribe-only join
      setStatus('connecting')
      const room = new Room()
      roomRef.current = room

      // Dedupe segment IDs — LiveKit re-emits the same final segment on minor
      // updates, which otherwise appears as duplicate transcript lines.
      const seen = new Set<string>()
      room.on(RoomEvent.TranscriptionReceived, (segments: TranscriptionSegment[], participant) => {
        const identity = participant?.identity || 'unknown'
        const who = identity.startsWith('sip_') || identity.includes('caller')
          ? 'Caller'
          : identity.includes('rescue-operator') || identity.includes('agent')
          ? 'Agent'
          : identity
        const fresh: { who: string; text: string; at: number }[] = []
        for (const s of segments) {
          if (!s.final || !s.text?.trim()) continue
          if (seen.has(s.id)) continue
          seen.add(s.id)
          fresh.push({ who, text: s.text, at: Date.now() })
        }
        if (fresh.length) setLines(prev => [...prev, ...fresh])
      })

      room.on(RoomEvent.Disconnected, () => {
        if (!cleaned) setStatus('ended')
      })

      try {
        await room.connect(livekit_url, lkToken)
        if (!cleaned) setStatus('live')
      } catch (e) {
        if (!cleaned) { setStatus('error'); setErrorMsg('Failed to connect to LiveKit room') }
      }

      void room_name  // (already in URL if we want to show it)
    }

    void join()

    return () => {
      cleaned = true
      roomRef.current?.disconnect()
    }
  }, [callId, token])

  const fmtTime = (s: number) => {
    const m = Math.floor(s / 60); const r = s % 60
    return `${m.toString().padStart(2, '0')}:${r.toString().padStart(2, '0')}`
  }

  return (
    <Layout title="Live Listener">
      <div className="max-w-4xl mx-auto p-4 md:p-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-zinc-500 dark:hover:text-zinc-100"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 overflow-hidden">
          {/* Header */}
          <div className="p-4 md:p-6 border-b border-slate-200 dark:border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                status === 'live' ? 'bg-red-500/10 ring-2 ring-red-500/30 animate-pulse' : 'bg-slate-100 dark:bg-zinc-800'
              }`}>
                <Mic className={`w-5 h-5 ${status === 'live' ? 'text-red-600' : 'text-slate-500'}`} />
              </div>
              <div>
                <p className="text-base font-semibold text-slate-900 dark:text-zinc-100">
                  Live Listener
                </p>
                <p className="text-xs text-slate-500 dark:text-zinc-500 font-mono">
                  Call: {callId?.slice(0, 8)}…
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold tabular text-slate-900 dark:text-zinc-100">{fmtTime(duration)}</p>
              <p className="text-[10px] uppercase tracking-wider text-slate-400 dark:text-zinc-600">
                {status === 'fetching_token' && 'Authorizing'}
                {status === 'connecting'     && 'Connecting'}
                {status === 'live'           && 'Listening'}
                {status === 'ended'          && 'Call ended'}
                {status === 'error'          && 'Error'}
              </p>
            </div>
          </div>

          {/* Error banner */}
          {status === 'error' && (
            <div className="m-4 p-3 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5" />
              <p className="text-sm text-red-700 dark:text-red-400">{errorMsg}</p>
            </div>
          )}

          {/* Transcript */}
          <div className="p-4 md:p-6 min-h-[400px] max-h-[60vh] overflow-y-auto">
            <h2 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-3">
              Live Transcript
            </h2>
            {lines.length === 0 && status === 'live' && (
              <p className="text-sm text-slate-400 dark:text-zinc-600 italic">
                Waiting for first utterance…
              </p>
            )}
            {lines.length === 0 && status !== 'live' && status !== 'error' && (
              <p className="text-sm text-slate-400 dark:text-zinc-600 italic">
                Connecting to live audio…
              </p>
            )}
            <div className="space-y-3">
              {lines.map((line, i) => (
                <div key={i} className="flex gap-3">
                  <span className={`text-xs font-semibold uppercase tracking-wider w-16 shrink-0 pt-0.5 ${
                    line.who === 'Caller' ? 'text-red-600 dark:text-red-400' : 'text-cyan-600 dark:text-cyan-400'
                  }`}>
                    {line.who}
                  </span>
                  <p className="text-sm text-slate-700 dark:text-zinc-300 leading-relaxed">
                    {line.text}
                  </p>
                </div>
              ))}
              <div ref={transcriptEndRef} />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
