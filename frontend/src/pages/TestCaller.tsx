import { useState, useEffect, useRef } from 'react'
import { Room, RoomEvent, Track, createLocalAudioTrack } from 'livekit-client'
import { Mic, MicOff, PhoneOff } from 'lucide-react'

type Status = 'connecting' | 'connected' | 'muted' | 'error' | 'ended'

export default function TestCaller() {
  const [status, setStatus] = useState<Status>('connecting')
  const [error, setError] = useState('')
  const roomRef = useRef<Room | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const livekit_url = params.get('livekit_url')

    if (!token || !livekit_url) {
      setError('Missing token or livekit_url in URL params. Open this page from the Live Call dashboard.')
      setStatus('error')
      return
    }

    let isCleanup = false
    const room = new Room()
    roomRef.current = room

    // Play any audio tracks published by remote participants (i.e. the agent's TTS)
    const attachedElements: HTMLAudioElement[] = []
    room.on(RoomEvent.TrackSubscribed, (track) => {
      if (track.kind === Track.Kind.Audio) {
        const el = track.attach() as HTMLAudioElement
        el.style.display = 'none'
        document.body.appendChild(el)
        el.play().catch(() => {})
        attachedElements.push(el)
      }
    })

    ;(async () => {
      try {
        await room.connect(livekit_url, token)
        if (isCleanup) return

        const audioTrack = await createLocalAudioTrack()
        await room.localParticipant.publishTrack(audioTrack)

        setStatus('connected')
      } catch (e) {
        if (!isCleanup) {
          setError(String(e))
          setStatus('error')
        }
      }
    })()

    return () => {
      isCleanup = true
      attachedElements.forEach(el => { el.pause(); el.remove() })
      room.disconnect()
    }
  }, [])

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
    roomRef.current?.disconnect()
    setStatus('ended')
  }

  const isActive = status === 'connected' || status === 'muted'

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
      <div className="bg-gray-800 rounded-2xl p-8 w-full max-w-sm text-center shadow-2xl border border-gray-700">
        <h1 className="text-xl font-bold text-white mb-1">Test Caller</h1>
        <p className="text-sm text-gray-400 mb-8">Simulates a phone caller for testing</p>

        {/* Status indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className={`w-3 h-3 rounded-full ${
            status === 'connected' ? 'bg-green-400 animate-pulse' :
            status === 'muted' ? 'bg-yellow-400' :
            status === 'connecting' ? 'bg-blue-400 animate-pulse' :
            status === 'ended' ? 'bg-gray-500' :
            'bg-red-500'
          }`} />
          <span className="text-sm font-medium text-gray-300">
            {status === 'connecting' && 'Connecting...'}
            {status === 'connected' && 'Live — agent can hear you'}
            {status === 'muted' && 'Muted'}
            {status === 'ended' && 'Call ended'}
            {status === 'error' && 'Connection error'}
          </span>
        </div>

        {/* Mic visualizer ring */}
        {isActive && (
          <div className={`w-24 h-24 rounded-full mx-auto mb-8 flex items-center justify-center border-4 ${
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
          <p className="text-sm text-red-400 mb-6 bg-red-900/30 rounded-lg p-3">{error}</p>
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

        {status === 'ended' && (
          <p className="text-gray-500 text-sm mt-4">You can close this tab.</p>
        )}

        <p className="text-xs text-gray-600 mt-8">
          In production this is replaced by a Twilio phone caller.
        </p>
      </div>
    </div>
  )
}
