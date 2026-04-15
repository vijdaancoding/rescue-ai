import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Room, RoomEvent, type TranscriptionSegment } from 'livekit-client'
import Layout from '../components/Layout'
import { AlertTriangle, Bell, Phone, Activity, Mic, PhoneOff, FlaskConical, ShieldAlert, Zap, Siren } from 'lucide-react'
import type { AnalysisData } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_WS_URL = API_URL.replace(/^http/, 'ws')

type ConnectionStatus = 'connecting' | 'connected' | 'error' | 'ended'

const URGENCY_COLOR: Record<string, string> = {
  critical: 'text-red-600',
  high: 'text-orange-500',
  medium: 'text-yellow-500',
  low: 'text-green-500',
}

const URGENCY_BG: Record<string, string> = {
  critical: 'bg-red-100 border-red-300',
  high: 'bg-orange-50 border-orange-300',
  medium: 'bg-yellow-50 border-yellow-300',
  low: 'bg-green-50 border-green-300',
}

const DISPATCH_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  police: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
  ambulance: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
  firefighters: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
}

const DISPATCH_LABEL: Record<string, string> = {
  police: 'Police',
  ambulance: 'Ambulance',
  firefighters: 'Firefighters',
}

export default function LiveCall() {
  const navigate = useNavigate()
  const [transcriptLines, setTranscriptLines] = useState<string[]>([])
  const [isRecording, setIsRecording] = useState(true)
  const [callerTestUrl, setCallerTestUrl] = useState<string | null>(null)
  const [callDuration, setCallDuration] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [callId, setCallId] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const dashboardWsRef = useRef<WebSocket | null>(null)
  const roomRef = useRef<Room | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement | null>(null)

  // Auto-scroll transcript to bottom
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcriptLines])

  // Call duration timer
  useEffect(() => {
    const timer = setInterval(() => setCallDuration(prev => prev + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  // WebSocket + LiveKit call setup
  useEffect(() => {
    let isCleanup = false
    const ws = new WebSocket(`${API_WS_URL}/ws/call`)
    wsRef.current = ws

    ws.onopen = () => setConnectionStatus('connecting')

    ws.onmessage = async (event) => {
      if (isCleanup) return
      let payload: { token: string; caller_token: string; room_name: string; livekit_url: string; call_id: string }
      try { payload = JSON.parse(event.data) } catch { return }

      const { token, caller_token, room_name, livekit_url, call_id } = payload
      setCallId(call_id)

      const params = new URLSearchParams({ token: caller_token, livekit_url, room_name })
      setCallerTestUrl(`/test-caller?${params.toString()}`)

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

    return () => {
      isCleanup = true
      ws.close()
      roomRef.current?.disconnect()
    }
  }, [])

  // Dashboard WebSocket — connect once callId is known
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

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const statusColor =
    connectionStatus === 'connected' ? 'text-green-300' :
    connectionStatus === 'error' || connectionStatus === 'ended' ? 'text-red-300' :
    'text-yellow-300'

  const statusLabel =
    connectionStatus === 'connecting' ? 'Connecting...' :
    connectionStatus === 'connected' ? 'Live' :
    connectionStatus === 'ended' ? 'Call Ended' : 'Connection Error'

  const spamPct = analysis ? Math.round(analysis.spam_score * 100) : null
  const urgencyPct = analysis ? Math.round(analysis.urgency_score * 100) : 34
  const urgencyLabel = analysis?.urgency_label ?? 'medium'
  const isSpam = analysis?.spam_label === 'spam'

  return (
    <Layout title="Active Call - Rescue AI">
      <div className="space-y-6">

        {/* Call Status Header */}
        <div className="card bg-gradient-to-r from-red-500 to-red-600 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center animate-pulse">
                <Phone className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">Emergency Call in Progress</h3>
                <p className="text-red-100">Caller ID: +92-XXX-XXX-XXXX</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold mb-1">{formatTime(callDuration)}</div>
              <div className="flex items-center gap-2 justify-end">
                <div className={`w-2 h-2 rounded-full animate-pulse ${connectionStatus === 'connected' ? 'bg-green-300' : 'bg-white'}`} />
                <span className={`text-sm ${statusColor}`}>{statusLabel}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <button
              onClick={() => setIsRecording(!isRecording)}
              className="btn bg-white/20 hover:bg-white/30 text-white border-0 backdrop-blur-md"
            >
              <Mic className="w-4 h-4 mr-2" />
              {isRecording ? 'Recording' : 'Paused'}
            </button>
            {callerTestUrl && (
              <a
                href={callerTestUrl}
                target="_blank"
                rel="noreferrer"
                className="btn bg-white/20 hover:bg-white/30 text-white border-0 backdrop-blur-md inline-flex items-center"
              >
                <FlaskConical className="w-4 h-4 mr-2" />
                Open Test Caller
              </a>
            )}
            <button
              onClick={handleEndCall}
              disabled={connectionStatus === 'ended'}
              className="btn bg-white hover:bg-gray-100 text-red-600 border-0 ml-auto disabled:opacity-50"
            >
              <PhoneOff className="w-4 h-4 mr-2" />
              End Call
            </button>
          </div>
        </div>

        {/* Live Urdu Transcription */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
              <Mic className="w-5 h-5 text-teal-600" />
              Live Transcription
            </h2>
            <div className="flex items-center gap-2">
              {/* Spam badge */}
              <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-semibold transition-all duration-500 ${
                spamPct === null
                  ? 'bg-gray-100 border-gray-200 text-gray-400'
                  : isSpam
                  ? 'bg-red-100 border-red-300 text-red-700'
                  : 'bg-green-100 border-green-300 text-green-700'
              }`}>
                <ShieldAlert className="w-3.5 h-3.5" />
                {spamPct === null ? 'Analysing...' : `Spam ${spamPct}%`}
              </div>
              {/* Urgency badge */}
              <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-semibold transition-all duration-500 ${
                analysis ? (URGENCY_BG[urgencyLabel] ?? 'bg-gray-100 border-gray-200') : 'bg-gray-100 border-gray-200 text-gray-400'
              }`}>
                <Zap className={`w-3.5 h-3.5 ${analysis ? (URGENCY_COLOR[urgencyLabel] ?? '') : 'text-gray-400'}`} />
                <span className={analysis ? (URGENCY_COLOR[urgencyLabel] ?? '') : 'text-gray-400'}>
                  {analysis ? urgencyLabel.toUpperCase() : 'Urgency...'}
                </span>
              </div>
            </div>
          </div>

          {/* Transcript display */}
          <div className="bg-gray-950 rounded-xl p-5 min-h-[160px] max-h-[280px] overflow-y-auto font-mono text-sm leading-relaxed">
            {connectionStatus === 'connecting' && (
              <p className="text-gray-500">Connecting to call...</p>
            )}
            {connectionStatus === 'error' && (
              <p className="text-red-400">Connection failed. Please try again.</p>
            )}
            {(connectionStatus === 'connected' || connectionStatus === 'ended') && transcriptLines.length === 0 && (
              <p className="text-gray-600">Waiting for speech<span className="animate-pulse">...</span></p>
            )}
            {transcriptLines.map((line, i) => (
              <p key={i} className="text-gray-100 mb-1">
                <span className="text-teal-500 mr-2 select-none">›</span>{line}
              </p>
            ))}
            <div ref={transcriptEndRef} />
          </div>

          {analysis && (
            <p className="mt-2 text-xs text-gray-400 text-right">
              Analysis #{analysis.analysis_count} · {analysis.transcript_word_count} words
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Situation Analysis */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-1 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
              AI Situation Analysis
            </h3>
            <p className="text-sm text-gray-500 mb-5">
              {analysis
                ? `Updated ${analysis.analysis_count} time${analysis.analysis_count !== 1 ? 's' : ''} this call`
                : 'Waiting for enough transcript (~20 words)...'}
            </p>

            {/* Urgency gauge */}
            <div className={`border-2 rounded-2xl p-5 mb-5 transition-all duration-700 ${URGENCY_BG[urgencyLabel] ?? 'bg-orange-50 border-orange-300'}`}>
              <div className="flex items-center gap-6">
                {/* Circle gauge */}
                <div className="relative flex-shrink-0">
                  <svg className="w-24 h-24" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="9" />
                    <circle
                      cx="50" cy="50" r="42" fill="none"
                      stroke={urgencyLabel === 'critical' ? '#ef4444' : urgencyLabel === 'high' ? '#f97316' : urgencyLabel === 'medium' ? '#eab308' : '#22c55e'}
                      strokeWidth="9"
                      strokeDasharray={`${urgencyPct * 2.639} 263.9`}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                      className="transition-all duration-1000"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <p className={`text-2xl font-bold ${URGENCY_COLOR[urgencyLabel] ?? 'text-gray-700'}`}>{urgencyPct}%</p>
                    <p className="text-xs font-semibold text-gray-500 uppercase">{urgencyLabel}</p>
                  </div>
                </div>

                {/* Analysis details */}
                <div className="flex-1 space-y-2 text-sm text-gray-700">
                  {analysis ? (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-500">ONNX spam</span>
                        <span className={`font-semibold ${isSpam ? 'text-red-600' : 'text-green-600'}`}>
                          {Math.round(analysis.onnx_spam_score * 100)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Gemini spam</span>
                        <span className={`font-semibold ${isSpam ? 'text-red-600' : 'text-green-600'}`}>
                          {Math.round(analysis.gemini_spam_score * 100)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Combined</span>
                        <span className={`font-bold ${isSpam ? 'text-red-600' : 'text-green-600'}`}>
                          {spamPct}% — {isSpam ? 'SPAM' : 'REAL'}
                        </span>
                      </div>
                      <p className="text-gray-600 italic pt-1 border-t border-gray-200/60 text-xs leading-snug">
                        {analysis.reasoning}
                      </p>
                    </>
                  ) : (
                    <p className="text-gray-400 italic text-xs">Awaiting analysis...</p>
                  )}
                </div>
              </div>

              {/* Dispatch recommendation */}
              {analysis && analysis.dispatch_recommendation.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200/60">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">AI Recommends Dispatching</p>
                  <div className="flex flex-wrap gap-2">
                    {analysis.dispatch_recommendation.map(type => {
                      const s = DISPATCH_STYLE[type]
                      return s ? (
                        <span key={type} className={`px-3 py-1 rounded-full text-xs font-bold border ${s.bg} ${s.text} ${s.border}`}>
                          {DISPATCH_LABEL[type]}
                        </span>
                      ) : null
                    })}
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-2 text-sm">
              <div className={`flex-1 rounded-lg p-2.5 text-center font-semibold ${isSpam ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                {spamPct === null ? 'Spam: Pending' : `Spam: ${spamPct}%`}
              </div>
              <div className={`flex-1 rounded-lg p-2.5 text-center font-semibold ${URGENCY_BG[urgencyLabel] ?? 'bg-orange-100'}`}>
                <span className={URGENCY_COLOR[urgencyLabel]}>
                  {urgencyLabel.charAt(0).toUpperCase() + urgencyLabel.slice(1)} Urgency
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h3>

            <div className="space-y-4">
              <button
                onClick={handleDispatch}
                disabled={!callId}
                className="w-full flex items-center gap-4 p-6 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-2xl border-0 text-white transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-xl"
              >
                <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center flex-shrink-0">
                  <Siren className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-xl font-bold">DISPATCH UNIT</p>
                  <p className="text-sm text-red-100">
                    {analysis?.dispatch_recommendation.length
                      ? `AI suggests: ${analysis.dispatch_recommendation.map(t => DISPATCH_LABEL[t]).join(', ')}`
                      : 'Select emergency services to deploy'}
                  </p>
                </div>
              </button>

              <button className="w-full flex items-center gap-4 p-6 bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 rounded-2xl border-0 text-white transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-xl">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center flex-shrink-0">
                  <Bell className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-xl font-bold">MARK AS FALSE ALARM</p>
                  <p className="text-sm text-yellow-100">Prank or non-emergency call</p>
                </div>
              </button>

              <button className="w-full flex items-center gap-4 p-6 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-2xl border-0 text-white transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-xl">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center flex-shrink-0">
                  <Phone className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-xl font-bold">TRANSFER CALL</p>
                  <p className="text-sm text-blue-100">Route to specialist</p>
                </div>
              </button>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Call Notes</label>
              <textarea
                placeholder="Add notes about this call..."
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="glass rounded-xl p-5 text-center shadow-lg">
          <p className="text-sm text-gray-700 font-medium">
            <span className="font-bold text-teal-600">Rescue AI</span> — Always ready to assist &nbsp;•&nbsp;
            Emergency Hotline: 1122 &nbsp;•&nbsp; Call Center: 123-456-7890
          </p>
        </div>
      </div>
    </Layout>
  )
}
