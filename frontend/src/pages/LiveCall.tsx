import { useState, useEffect, useRef, useCallback } from 'react'
import { Room, RoomEvent, type TranscriptionSegment } from 'livekit-client'
import Layout from '../components/Layout'
import { AlertTriangle, Bell, Phone, Volume2, Activity, Mic, PhoneOff, FlaskConical } from 'lucide-react'

const API_WS_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  .replace(/^http/, 'ws')

type ConnectionStatus = 'connecting' | 'connected' | 'error' | 'ended'

export default function LiveCall() {
  const [transcriptLines, setTranscriptLines] = useState<string[]>([])
  const [soundWave, setSoundWave] = useState<number[]>([])
  const [isRecording, setIsRecording] = useState(true)
  const [callerTestUrl, setCallerTestUrl] = useState<string | null>(null)
  const [callDuration, setCallDuration] = useState(0)
  const [threatLevel] = useState(34)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')

  const wsRef = useRef<WebSocket | null>(null)
  const roomRef = useRef<Room | null>(null)

  // Simulate sound wave animation
  useEffect(() => {
    const interval = setInterval(() => {
      setSoundWave(Array.from({ length: 60 }, () => Math.random() * 100))
    }, 100)
    return () => clearInterval(interval)
  }, [])

  // Call duration timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCallDuration(prev => prev + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // WebSocket + LiveKit setup
  useEffect(() => {
    // `isCleanup` is scoped to this effect closure. When React StrictMode
    // runs cleanup and re-runs the effect, the first closure's isCleanup
    // becomes true so its onclose/onmessage won't update state. The second
    // closure starts fresh with isCleanup=false and opens a new WebSocket.
    let isCleanup = false

    const ws = new WebSocket(`${API_WS_URL}/ws/call`)
    wsRef.current = ws

    ws.onopen = () => setConnectionStatus('connecting')

    ws.onmessage = async (event) => {
      if (isCleanup) return

      let payload: { token: string; caller_token: string; room_name: string; livekit_url: string; call_id: string }
      try {
        payload = JSON.parse(event.data)
      } catch {
        return
      }

      const { token, caller_token, room_name, livekit_url } = payload

      // Build the test caller URL so the dispatcher can open a second tab
      const params = new URLSearchParams({ token: caller_token, livekit_url, room_name })
      setCallerTestUrl(`/test-caller?${params.toString()}`)

      const room = new Room()
      roomRef.current = room

      room.on(RoomEvent.TranscriptionReceived, (segments: TranscriptionSegment[]) => {
        const finalTexts = segments
          .filter((s) => s.final)
          .map((s) => s.text)
          .filter(Boolean)
        if (finalTexts.length > 0) {
          setTranscriptLines((prev) => [...prev, ...finalTexts])
        }
      })

      try {
        // Dispatcher joins as subscribe-only — no mic publishing
        await room.connect(livekit_url, token)
        setConnectionStatus('connected')
      } catch {
        setConnectionStatus('error')
      }
    }

    ws.onerror = () => setConnectionStatus('error')

    ws.onclose = () => {
      // Ignore close events triggered by our own cleanup (StrictMode or unmount)
      if (isCleanup) return
      setConnectionStatus('ended')
    }

    return () => {
      isCleanup = true
      ws.close()
      roomRef.current?.disconnect()
    }
  }, [])

  const handleEndCall = useCallback(() => {
    setConnectionStatus('ended')
    wsRef.current?.send('end_call')
    wsRef.current?.close()
    roomRef.current?.disconnect()
  }, [])


  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const transcriptText = transcriptLines.join('\n')

  const statusColor =
    connectionStatus === 'connected'
      ? 'text-green-300'
      : connectionStatus === 'error' || connectionStatus === 'ended'
      ? 'text-red-300'
      : 'text-yellow-300'

  const statusLabel =
    connectionStatus === 'connecting'
      ? 'Connecting...'
      : connectionStatus === 'connected'
      ? 'Live'
      : connectionStatus === 'ended'
      ? 'Call Ended'
      : 'Connection Error'

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
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
              <Mic className="w-6 h-6 text-teal-600" />
              Live Urdu Transcription
            </h2>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 rounded-full border border-red-200">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium text-red-700">Recording</span>
              </div>
              <span className="badge badge-info">Urdu Detected</span>
            </div>
          </div>

          <div className="flex gap-3 mb-6">
            <button className="btn btn-secondary text-sm">
              Prank Probability: 7%
            </button>
            <button className="btn btn-primary text-sm">
              TTS (URDU-A)
            </button>
            <button className="btn btn-secondary text-sm">
              Auto-Translate
            </button>
          </div>

          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 min-h-[150px] border-2 border-gray-200">
            <textarea
              value={connectionStatus === 'connecting'
                ? 'Connecting to call...'
                : connectionStatus === 'error'
                ? 'Connection failed. Please try again.'
                : transcriptText || 'Waiting for speech...'}
              readOnly
              placeholder="Urdu transcription will appear here as the caller speaks..."
              className="w-full h-32 bg-transparent border-none focus:outline-none resize-none text-gray-900 text-lg"
            />
          </div>

          <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
            <span>Confidence: 94%</span>
            <span>Words: {transcriptText.split(/\s+/).filter(Boolean).length}</span>
            <span>Language: Urdu</span>
          </div>
        </div>

        {/* Sound Wave Visualizer */}
        <div className="card bg-gradient-to-br from-gray-900 to-gray-800 text-white">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Volume2 className="w-6 h-6 text-teal-400" />
              <h3 className="text-xl font-bold">Sound Wave Visualizer</h3>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-400" />
              <span className="text-sm text-gray-300">Active</span>
            </div>
          </div>
          <p className="text-sm text-gray-400 mb-6">Real-time audio waveform analysis</p>

          {/* Waveform Display */}
          <div className="bg-black/30 backdrop-blur-md rounded-xl p-8 h-56 flex items-center justify-center border border-white/10">
            <div className="flex items-end justify-center gap-1 h-40 w-full">
              {soundWave.map((height, index) => (
                <div
                  key={index}
                  className="flex-1 bg-gradient-to-t from-teal-500 via-teal-400 to-teal-300 rounded-t transition-all duration-100 shadow-lg"
                  style={{
                    height: `${height}%`,
                    boxShadow: height > 70 ? '0 0 10px rgba(20, 184, 166, 0.5)' : 'none'
                  }}
                />
              ))}
            </div>
          </div>

          {/* Audio Metrics */}
          <div className="mt-6 grid grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-center">
              <p className="text-sm text-gray-400 mb-1">Volume</p>
              <p className="text-2xl font-bold text-white">78 dB</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-center">
              <p className="text-sm text-gray-400 mb-1">Pitch</p>
              <p className="text-2xl font-bold text-white">245 Hz</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-center">
              <p className="text-sm text-gray-400 mb-1">Emotion</p>
              <p className="text-2xl font-bold text-yellow-400">Urgent</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-center">
              <p className="text-sm text-gray-400 mb-1">Quality</p>
              <p className="text-2xl font-bold text-green-400">HD</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Situation Overview */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
              AI Situation Analysis
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Real-time threat assessment and recommendations
            </p>

            <div className="bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-300 rounded-2xl p-6 mb-6">
              <div className="text-center mb-6">
                <div className="relative inline-block">
                  <svg className="w-32 h-32" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#ef4444"
                      strokeWidth="8"
                      strokeDasharray={`${threatLevel * 2.827} 282.7`}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                      className="transition-all duration-1000"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div>
                      <p className="text-4xl font-bold text-red-600">{threatLevel}%</p>
                      <p className="text-sm text-gray-600 font-semibold">CRITICAL</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-5 shadow-md">
                <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-red-600" />
                  AI Analysis Report
                </h4>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-red-600 font-bold">•</span>
                    <span>High-priority emergency detected</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-600 font-bold">•</span>
                    <span>Caller shows signs of distress (voice trembling detected)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-600 font-bold">•</span>
                    <span>Keywords: "emergency", "help", "urgent" detected</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 font-bold">•</span>
                    <span>Location identified: Model Town, Lahore</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="flex gap-2 text-sm">
              <div className="flex-1 bg-red-100 text-red-700 rounded-lg p-3 text-center font-semibold">
                Confidence: 94%
              </div>
              <div className="flex-1 bg-orange-100 text-orange-700 rounded-lg p-3 text-center font-semibold">
                Response Time: 3m
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h3>

            <div className="space-y-4">
              <button className="w-full flex items-center gap-4 p-6 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 rounded-2xl border-0 text-white transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-xl">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-xl font-bold">DISPATCH UNIT</p>
                  <p className="text-sm text-red-100">Send ambulance immediately</p>
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

            {/* Call Notes */}
            <div className="mt-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Call Notes
              </label>
              <textarea
                placeholder="Add notes about this call..."
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="glass rounded-xl p-6 text-center shadow-lg">
          <p className="text-sm text-gray-700 font-medium">
            <span className="font-bold text-teal-600">Rescue AI</span> - Always ready to assist  •
            Emergency Hotline: 1122  •  Call Center: 123-456-7890
          </p>
        </div>
      </div>
    </Layout>
  )
}
