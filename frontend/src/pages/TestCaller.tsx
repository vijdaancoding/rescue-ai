import { useState, useEffect, useRef } from 'react'
import { Room, RoomEvent, Track, createLocalAudioTrack } from 'livekit-client'
import { Mic, MicOff, PhoneOff, Phone, AlertTriangle } from 'lucide-react'

type Status = 'idle' | 'connecting' | 'connected' | 'muted' | 'error' | 'ended'

export default function TestCaller() {
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState('')
  const [missingParams, setMissingParams] = useState(false)
  const roomRef = useRef<Room | null>(null)
  const attachedElementsRef = useRef<HTMLAudioElement[]>([])

  // Early param check — don't start until we know the URL is usable.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const livekit_url = params.get('livekit_url')
    if (!token || !livekit_url) {
      setMissingParams(true)
      setError('Missing token or livekit_url in URL. Open this page from the Live Call dashboard.')
      setStatus('error')
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      attachedElementsRef.current.forEach(el => { el.pause(); el.remove() })
      roomRef.current?.disconnect()
    }
  }, [])

  // The meaningful work runs ONLY after a user gesture (Start Call button).
  // This guarantees the browser lets us play the agent's audio — without a user
  // gesture, <audio>.play() is silently blocked by autoplay policy and you get
  // a connected call with no agent voice.
  const handleStart = async () => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')!
    const livekit_url = params.get('livekit_url')!

    setStatus('connecting')
    setError('')

    const room = new Room()
    roomRef.current = room

    // Attach any audio tracks published by remote participants (the agent's TTS).
    room.on(RoomEvent.TrackSubscribed, (track) => {
      if (track.kind !== Track.Kind.Audio) return
      const el = track.attach() as HTMLAudioElement
      el.style.display = 'none'
      document.body.appendChild(el)
      attachedElementsRef.current.push(el)
      el.play().catch(err => {
        // Shouldn't happen now — user just clicked Start — but log clearly if it does.
        console.error('Audio play blocked:', err)
        setError('Audio playback blocked by browser. Try clicking End + Start again.')
      })
    })

    try {
      // Grab the mic FIRST so permission prompt resolves before we pull in the
      // agent's audio. Once granted, the page is fully gesture-authorized for
      // both input and output.
      const audioTrack = await createLocalAudioTrack()
      await room.connect(livekit_url, token)
      await room.localParticipant.publishTrack(audioTrack)
      setStatus('connected')
    } catch (e) {
      console.error('TestCaller connect failed:', e)
      setError(String((e as Error)?.message || e))
      setStatus('error')
    }
  }

  const handleMute = () => {
    const room = roomRef.current
    if (!room) return
    if (status === 'connected') {
      room.localParticipant.setMicrophoneEnabled(false)
      setStatus('muted')
    } else if (status === 'muted') {
      room.localParticipant.setMicrophoneEnabled(true)
      setStatus('connected')
    }
  }

  const handleEnd = () => {
    attachedElementsRef.current.forEach(el => { el.pause(); el.remove() })
    attachedElementsRef.current = []
    roomRef.current?.disconnect()
    roomRef.current = null
    setStatus('ended')
  }

  const isActive = status === 'connected' || status === 'muted'

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
      <div className="bg-gray-800 rounded-2xl p-8 w-full max-w-sm text-center shadow-2xl border border-gray-700">
        <h1 className="text-xl font-bold text-white mb-1">Test Caller</h1>
        <p className="text-sm text-gray-400 mb-8">Simulates a phone caller for testing</p>

        {/* Status indicator */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className={`w-3 h-3 rounded-full ${
            status === 'connected' ? 'bg-green-400 animate-pulse' :
            status === 'muted' ? 'bg-yellow-400' :
            status === 'connecting' ? 'bg-blue-400 animate-pulse' :
            status === 'ended' ? 'bg-gray-500' :
            status === 'idle' ? 'bg-gray-400' :
            'bg-red-500'
          }`} />
          <span className="text-sm font-medium text-gray-300">
            {status === 'idle'       && 'Ready'}
            {status === 'connecting' && 'Connecting...'}
            {status === 'connected'  && 'Live — agent can hear you'}
            {status === 'muted'      && 'Muted'}
            {status === 'ended'      && 'Call ended'}
            {status === 'error'      && 'Connection error'}
          </span>
        </div>

        {/* Mic visualizer ring */}
        {isActive && (
          <div className={`w-24 h-24 rounded-full mx-auto mb-6 flex items-center justify-center border-4 ${
            status === 'connected'
              ? 'border-green-400 bg-green-400/10 animate-pulse'
              : 'border-yellow-400 bg-yellow-400/10'
          }`}>
            {status === 'connected'
              ? <Mic className="w-10 h-10 text-green-400" />
              : <MicOff className="w-10 h-10 text-yellow-400" />
            }
          </div>
        )}

        {error && (
          <div className="mb-6 flex items-start gap-2 bg-red-900/30 rounded-lg p-3 text-left">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* Start button — visible only until we're live */}
        {(status === 'idle' || status === 'ended' || status === 'error') && !missingParams && (
          <>
            <p className="text-xs text-gray-500 mb-4 leading-relaxed">
              Click below to start the test call. Your browser will ask for mic
              permission — the agent will greet you in Urdu once connected.
            </p>
            <button
              onClick={handleStart}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-semibold text-sm bg-green-600 hover:bg-green-500 text-white transition-colors"
            >
              <Phone className="w-4 h-4" />
              {status === 'ended' || status === 'error' ? 'Start Again' : 'Start Test Call'}
            </button>
          </>
        )}

        {isActive && (
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleMute}
              className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm bg-gray-700 hover:bg-gray-600 text-white transition-colors"
            >
              {status === 'muted'
                ? <><Mic className="w-4 h-4" /> Unmute</>
                : <><MicOff className="w-4 h-4" /> Mute</>
              }
            </button>
            <button
              onClick={handleEnd}
              className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm bg-red-600 hover:bg-red-700 text-white transition-colors"
            >
              <PhoneOff className="w-4 h-4" /> End
            </button>
          </div>
        )}

        <p className="text-xs text-gray-600 mt-8">
          In production this is replaced by a Twilio phone caller.
        </p>
      </div>
    </div>
  )
}
