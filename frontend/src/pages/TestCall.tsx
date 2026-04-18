import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Room, RoomEvent, type TranscriptionSegment } from 'livekit-client'
import Layout from '../components/Layout'
import { AlertTriangle, Activity, Mic, PhoneOff, ShieldAlert, Zap, Siren, Bell, FlaskConical } from 'lucide-react'
import type { AnalysisData } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_WS_URL = API_URL.replace(/^http/, 'ws')

type ConnectionStatus = 'connecting' | 'connected' | 'error' | 'ended'

const URGENCY_RING: Record<string, string> = {
  critical: 'bg-red-50 border-red-200 dark:bg-red-500/10 dark:border-red-500/40',
  high:     'bg-orange-50 border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/40',
  medium:   'bg-amber-50 border-amber-200 dark:bg-amber-500/10 dark:border-amber-500/40',
  low:      'bg-emerald-50 border-emerald-200 dark:bg-emerald-500/10 dark:border-emerald-500/40',
}

const URGENCY_COLOR: Record<string, string> = {
  critical: 'text-red-600 dark:text-red-400',
  high:     'text-orange-600 dark:text-orange-400',
  medium:   'text-amber-600 dark:text-amber-400',
  low:      'text-emerald-600 dark:text-emerald-400',
}

const DISPATCH_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  police:      { bg: 'bg-blue-50 dark:bg-blue-500/10',     text: 'text-blue-700 dark:text-blue-400',   border: 'border-blue-200 dark:border-blue-500/30' },
  ambulance:   { bg: 'bg-red-50 dark:bg-red-500/10',       text: 'text-red-700 dark:text-red-400',     border: 'border-red-200 dark:border-red-500/30' },
  firefighters:{ bg: 'bg-orange-50 dark:bg-orange-500/10', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-200 dark:border-orange-500/30' },
}

const DISPATCH_LABEL: Record<string, string> = {
  police: 'Police', ambulance: 'Ambulance', firefighters: 'Firefighters',
}

export default function TestCall() {
  const navigate = useNavigate()
  const [transcriptLines, setTranscriptLines] = useState<string[]>([])
  const [callDuration, setCallDuration] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [callId, setCallId] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
  const [callerTestUrl, setCallerTestUrl] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const dashboardWsRef = useRef<WebSocket | null>(null)
  const roomRef = useRef<Room | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcriptLines])

  useEffect(() => {
    const timer = setInterval(() => setCallDuration(prev => prev + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    let isCleanup = false

    const openWebSocket = (lat?: number, lng?: number) => {
      const params = lat != null && lng != null ? `?lat=${lat}&lng=${lng}` : ''
      const ws = new WebSocket(`${API_WS_URL}/ws/call${params}`)
      wsRef.current = ws

      ws.onopen = () => setConnectionStatus('connecting')

    ws.onmessage = async (event) => {
      if (isCleanup) return
      let payload: { token: string; caller_token: string; room_name: string; livekit_url: string; call_id: string }
      try { payload = JSON.parse(event.data) } catch { return }

      const { token, caller_token, room_name, livekit_url, call_id } = payload
      setCallId(call_id)

      // Build the test caller URL so a second tab can simulate the caller
      const testParams = new URLSearchParams({ token: caller_token, livekit_url, room_name })
      setCallerTestUrl(`/test-caller?${testParams.toString()}`)

      const room = new Room()
      roomRef.current = room

      room.on(RoomEvent.TranscriptionReceived, (segments: TranscriptionSegment[]) => {
        const finalTexts = segments.filter(s => s.final).map(s => s.text).filter(Boolean)
        if (finalTexts.length > 0) setTranscriptLines(prev => [...prev, ...finalTexts])
      })

      try {
        await room.connect(livekit_url, token)
        setConnectionStatus('connected')
      } catch {
        setConnectionStatus('error')
      }
    }

      ws.onerror = () => setConnectionStatus('error')
      ws.onclose = () => { if (!isCleanup) setConnectionStatus('ended') }
    }

    // Request GPS before connecting — agent uses it to skip asking for location.
    // If denied or unavailable, fall through and open the WebSocket without coords.
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => { if (!isCleanup) openWebSocket(pos.coords.latitude, pos.coords.longitude) },
        ()      => { if (!isCleanup) openWebSocket() },
        { timeout: 5000, maximumAge: 60000 },
      )
    } else {
      openWebSocket()
    }

    return () => {
      isCleanup = true
      wsRef.current?.close()
      roomRef.current?.disconnect()
    }
  }, [])

  useEffect(() => {
    if (!callId) return
    let isCleanup = false
    const dws = new WebSocket(`${API_WS_URL}/ws/dashboard`)
    dashboardWsRef.current = dws

    dws.onmessage = (event) => {
      if (isCleanup) return
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'analysis_update' && data.call_id === callId) {
          setAnalysis(data as AnalysisData)
        }
      } catch { /* ignore */ }
    }

    return () => { isCleanup = true; dws.close() }
  }, [callId])

  const handleEndCall = useCallback(() => {
    setConnectionStatus('ended')
    wsRef.current?.send('end_call')
    wsRef.current?.close()
    roomRef.current?.disconnect()
  }, [])

  const handleDispatch = useCallback(() => {
    if (!callId) return
    navigate(`/dispatch/${callId}`, { state: { analysis } })
  }, [callId, analysis, navigate])

  const handleFalseAlarm = useCallback(async () => {
    if (callId) {
      await fetch(`${API_URL}/calls/${callId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'FalseAlarm' }),
      }).catch(() => {})
    }
    handleEndCall()
    navigate('/dashboard')
  }, [callId, handleEndCall, navigate])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const spamPct = analysis ? Math.round(analysis.spam_score * 100) : null
  const urgencyPct = analysis ? Math.round(analysis.urgency_score * 100) : 34
  const urgencyLabel = analysis?.urgency_label ?? 'medium'
  const isSpam = analysis?.spam_label === 'spam'

  const statusDot =
    connectionStatus === 'connected' ? 'bg-emerald-500' :
    connectionStatus === 'error' || connectionStatus === 'ended' ? 'bg-red-500' :
    'bg-amber-400'

  const statusLabel =
    connectionStatus === 'connecting' ? 'Connecting...' :
    connectionStatus === 'connected' ? 'Live' :
    connectionStatus === 'ended' ? 'Call Ended' : 'Connection Error'

  return (
    <Layout title="Browser Test Call">
      <div className="space-y-4">

        {/* Call header bar */}
        <div className="bg-amber-50 border border-amber-200 dark:bg-amber-500/5 dark:border-amber-500/25 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-11 h-11 bg-amber-100 dark:bg-amber-500/15 rounded-xl flex items-center justify-center">
                <FlaskConical className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-base font-semibold text-slate-900 dark:text-zinc-100">Browser Test Call</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${statusDot}`} />
                  <span className="text-xs text-slate-500 dark:text-zinc-500">{statusLabel}</span>
                  <span className="text-slate-300 dark:text-zinc-700">·</span>
                  <span className="text-xs text-slate-500 dark:text-zinc-500">Browser mic — no Twilio</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-2xl font-bold tabular text-slate-900 dark:text-zinc-100">{formatTime(callDuration)}</p>
                <p className="text-xs text-slate-400 dark:text-zinc-600">Duration</p>
              </div>
              {callerTestUrl && (
                <a
                  href={callerTestUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 hover:border-cyan-300 text-slate-600 hover:text-cyan-600
                    dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:border-zinc-700 dark:hover:border-cyan-500/50 dark:text-zinc-300 dark:hover:text-cyan-400
                    rounded-lg text-sm font-medium transition-all duration-200"
                >
                  <FlaskConical className="w-4 h-4" />
                  Test Caller
                </a>
              )}
              <button
                onClick={handleEndCall}
                disabled={connectionStatus === 'ended'}
                className="flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 hover:border-red-300 text-slate-600 hover:text-red-600
                  dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:border-zinc-700 dark:hover:border-red-500/50 dark:text-zinc-300 dark:hover:text-red-400
                  rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
              >
                <PhoneOff className="w-4 h-4" />
                End Call
              </button>
            </div>
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: Transcript */}
          <div className="card flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Mic className="w-4 h-4 text-teal-600 dark:text-cyan-400" />
                <h2 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider">Live Transcript</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold ${
                  spamPct === null
                    ? 'bg-slate-100 border-slate-200 text-slate-400 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-500'
                    : isSpam
                    ? 'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:border-red-500/25 dark:text-red-400'
                    : 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/25 dark:text-emerald-400'
                }`}>
                  <ShieldAlert className="w-3 h-3" />
                  {spamPct === null ? 'Analysing...' : `Spam ${spamPct}%`}
                </span>
                <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold ${
                  analysis
                    ? (URGENCY_RING[urgencyLabel] ?? 'bg-slate-100 border-slate-200 dark:bg-zinc-800 dark:border-zinc-700')
                    : 'bg-slate-100 border-slate-200 text-slate-400 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-500'
                }`}>
                  <Zap className={`w-3 h-3 ${analysis ? (URGENCY_COLOR[urgencyLabel] ?? '') : 'text-slate-400 dark:text-zinc-500'}`} />
                  <span className={analysis ? (URGENCY_COLOR[urgencyLabel] ?? '') : 'text-slate-400 dark:text-zinc-500'}>
                    {analysis ? urgencyLabel.toUpperCase() : 'Urgency...'}
                  </span>
                </span>
              </div>
            </div>

            <div className="bg-slate-950 rounded-xl p-4 flex-1 min-h-[180px] max-h-[320px] overflow-y-auto font-mono text-sm leading-relaxed border border-slate-800">
              {connectionStatus === 'connecting' && (
                <p className="text-slate-600 text-xs">Connecting to call...</p>
              )}
              {connectionStatus === 'error' && (
                <p className="text-red-400 text-xs">Connection failed. Please try again.</p>
              )}
              {(connectionStatus === 'connected' || connectionStatus === 'ended') && transcriptLines.length === 0 && (
                <p className="text-slate-700 text-xs">Waiting for speech<span className="animate-pulse">...</span></p>
              )}
              {transcriptLines.map((line, i) => (
                <p key={i} className="text-slate-200 mb-1 text-xs">
                  <span className="text-cyan-500 mr-2 select-none">›</span>{line}
                </p>
              ))}
              <div ref={transcriptEndRef} />
            </div>

            {analysis && (
              <p className="mt-2 text-xs text-slate-400 dark:text-zinc-600 text-right">
                Analysis #{analysis.analysis_count} · {analysis.transcript_word_count} words
              </p>
            )}
          </div>

          {/* Right: AI Analysis */}
          <div className="card flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <h2 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider">AI Situation Analysis</h2>
            </div>
            <p className="text-xs text-slate-400 dark:text-zinc-600 mb-4">
              {analysis
                ? `Updated ${analysis.analysis_count} time${analysis.analysis_count !== 1 ? 's' : ''} this call`
                : 'Waiting for enough transcript (~20 words)...'}
            </p>

            {/* Urgency gauge */}
            <div className={`border rounded-xl p-4 mb-4 transition-all duration-700 ${URGENCY_RING[urgencyLabel] ?? 'bg-amber-50 border-amber-200 dark:bg-amber-500/10 dark:border-amber-500/40'}`}>
              <div className="flex items-center gap-5">
                <div className="relative flex-shrink-0">
                  <svg className="w-20 h-20" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" className="dark:stroke-zinc-800" />
                    <circle
                      cx="50" cy="50" r="42" fill="none"
                      stroke={urgencyLabel === 'critical' ? '#ef4444' : urgencyLabel === 'high' ? '#f97316' : urgencyLabel === 'medium' ? '#f59e0b' : '#10b981'}
                      strokeWidth="8"
                      strokeDasharray={`${urgencyPct * 2.639} 263.9`}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                      className="transition-all duration-1000"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <p className={`text-xl font-bold tabular ${URGENCY_COLOR[urgencyLabel] ?? 'text-slate-500'}`}>{urgencyPct}%</p>
                    <p className="text-[10px] font-semibold text-slate-400 dark:text-zinc-500 uppercase">{urgencyLabel}</p>
                  </div>
                </div>

                <div className="flex-1 space-y-2 text-xs">
                  {analysis ? (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 dark:text-zinc-500">ONNX spam</span>
                        <span className={`font-semibold tabular ${isSpam ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          {Math.round(analysis.onnx_spam_score * 100)}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 dark:text-zinc-500">Gemini spam</span>
                        <span className={`font-semibold tabular ${isSpam ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          {Math.round(analysis.gemini_spam_score * 100)}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center border-t border-slate-200 dark:border-zinc-800 pt-2">
                        <span className="text-slate-400 dark:text-zinc-500">Combined</span>
                        <span className={`font-bold tabular ${isSpam ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          {spamPct}% — {isSpam ? 'SPAM' : 'REAL'}
                        </span>
                      </div>
                      <p className="text-slate-500 dark:text-zinc-500 italic pt-1 leading-snug text-[11px]">
                        {analysis.reasoning}
                      </p>
                    </>
                  ) : (
                    <p className="text-slate-400 dark:text-zinc-600 italic text-xs">Awaiting analysis...</p>
                  )}
                </div>
              </div>

              {analysis && analysis.dispatch_recommendation.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200/80 dark:border-zinc-800/60">
                  <p className="text-[10px] font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Activity className="w-3 h-3" /> AI Recommends
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.dispatch_recommendation.map(type => {
                      const s = DISPATCH_STYLE[type]
                      return s ? (
                        <span key={type} className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${s.bg} ${s.text} ${s.border}`}>
                          {DISPATCH_LABEL[type]}
                        </span>
                      ) : null
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Status pills */}
            <div className="grid grid-cols-2 gap-2 text-xs mb-4">
              <div className={`rounded-lg p-2.5 text-center font-semibold border ${
                isSpam
                  ? 'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:border-red-500/25 dark:text-red-400'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/25 dark:text-emerald-400'
              }`}>
                {spamPct === null ? 'Spam: Pending' : `Spam: ${spamPct}%`}
              </div>
              <div className={`rounded-lg p-2.5 text-center font-semibold border ${URGENCY_RING[urgencyLabel] ?? 'bg-amber-50 border-amber-200'}`}>
                <span className={URGENCY_COLOR[urgencyLabel]}>
                  {urgencyLabel.charAt(0).toUpperCase() + urgencyLabel.slice(1)} Urgency
                </span>
              </div>
            </div>

            {/* Call notes */}
            <div className="mt-auto">
              <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Call Notes</label>
              <textarea
                placeholder="Add notes about this call..."
                className="w-full px-3 py-2.5 rounded-lg resize-none text-sm transition-all duration-200
                  bg-slate-50 border border-slate-200 text-slate-900 placeholder:text-slate-400
                  dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-200 dark:placeholder:text-zinc-600
                  focus:outline-none focus:ring-1 focus:ring-teal-500 dark:focus:ring-cyan-500"
                rows={2}
              />
            </div>
          </div>
        </div>

        {/* Action bar */}
        <div className="flex gap-3 pt-1">
          <button
            onClick={handleFalseAlarm}
            className="flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium transition-all duration-200
              bg-white border border-slate-200 text-slate-500 hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700
              dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-amber-500/10 dark:hover:border-amber-500/40 dark:hover:text-amber-400"
          >
            <Bell className="w-4 h-4" />
            Mark as False Alarm
          </button>

          <button
            onClick={handleDispatch}
            disabled={!callId}
            className="flex-1 flex items-center justify-center gap-3 py-3 bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-white font-semibold text-base transition-all duration-200 active:scale-[0.99] shadow-lg shadow-red-500/20"
          >
            <Siren className="w-5 h-5" />
            <span>DISPATCH UNIT</span>
            {analysis?.dispatch_recommendation?.length ? (
              <span className="text-xs text-red-200 font-normal">
                AI: {analysis.dispatch_recommendation.map(t => DISPATCH_LABEL[t]).join(', ')}
              </span>
            ) : null}
          </button>
        </div>
      </div>
    </Layout>
  )
}
