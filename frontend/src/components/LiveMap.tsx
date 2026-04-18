import { useMemo } from 'react'
import { APIProvider, Map, AdvancedMarker, Pin } from '@vis.gl/react-google-maps'
import { MapPin, AlertTriangle } from 'lucide-react'
import type { CallSummary } from '../types'

const GMAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
// Static map id not required for vector maps, but one must be provided for
// AdvancedMarker support — using Google's default "DEMO_MAP_ID" shipped with
// the library works for prototypes.
const MAP_ID = 'DEMO_MAP_ID'

// Pakistan center — used as fallback when no calls have GPS.
const PAKISTAN_CENTER = { lat: 30.3753, lng: 69.3451 }

// Fake rescue units for visual demo — real fleet tracking is a future feature.
// Positioned around major Pakistan cities.
const MOCK_UNITS: { lat: number; lng: number; kind: 'enroute' | 'available' | 'standby' }[] = [
  { lat: 31.5204, lng: 74.3587, kind: 'enroute'   }, // Lahore
  { lat: 24.8607, lng: 67.0011, kind: 'available' }, // Karachi
  { lat: 33.6844, lng: 73.0479, kind: 'standby'   }, // Islamabad
]

const UNIT_PIN: Record<string, { background: string; borderColor: string; glyphColor: string }> = {
  enroute:   { background: '#06b6d4', borderColor: '#0891b2', glyphColor: '#ffffff' }, // cyan
  available: { background: '#10b981', borderColor: '#059669', glyphColor: '#ffffff' }, // emerald
  standby:   { background: '#f59e0b', borderColor: '#d97706', glyphColor: '#ffffff' }, // amber
}

function callPinColor(call: CallSummary): { background: string; borderColor: string; glyphColor: string } {
  if (call.status === 'Active')      return { background: '#ef4444', borderColor: '#dc2626', glyphColor: '#ffffff' } // red Emergency
  if (call.status === 'Dispatched')  return { background: '#f97316', borderColor: '#ea580c', glyphColor: '#ffffff' } // orange
  if (call.spam_label === 'spam')    return { background: '#6b7280', borderColor: '#4b5563', glyphColor: '#ffffff' } // grey-muted
  return                                    { background: '#6366f1', borderColor: '#4f46e5', glyphColor: '#ffffff' } // indigo — recent benign
}

interface LiveMapProps {
  calls: CallSummary[]
}

export default function LiveMap({ calls }: LiveMapProps) {
  // Keep only calls that have real coordinates.
  const placedCalls = useMemo(() => calls.filter(c => c.lat != null && c.lng != null), [calls])

  const center = useMemo(() => {
    // Prefer an Active call; else most recent placed call; else Pakistan center.
    const active = placedCalls.find(c => c.status === 'Active')
    if (active) return { lat: active.lat!, lng: active.lng! }
    if (placedCalls.length) return { lat: placedCalls[0].lat!, lng: placedCalls[0].lng! }
    return PAKISTAN_CENTER
  }, [placedCalls])

  if (!GMAPS_API_KEY) {
    return (
      <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 dark:border-zinc-800 relative flex items-center justify-center p-8" style={{ minHeight: '400px' }}>
        <div className="flex items-start gap-3 text-amber-700 dark:text-amber-400">
          <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold">Map disabled</p>
            <p className="text-sm mt-1">
              <code>VITE_GOOGLE_MAPS_API_KEY</code> not set at build time.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 dark:border-zinc-800 relative" style={{ minHeight: '400px' }}>
      <APIProvider apiKey={GMAPS_API_KEY}>
        <Map
          mapId={MAP_ID}
          defaultCenter={center}
          defaultZoom={placedCalls.length ? 10 : 5}
          gestureHandling="greedy"
          disableDefaultUI={false}
          mapTypeControl={false}
          streetViewControl={false}
          fullscreenControl={false}
        >
          {/* Real call pins */}
          {placedCalls.map(call => {
            const p = callPinColor(call)
            return (
              <AdvancedMarker
                key={call.id}
                position={{ lat: call.lat!, lng: call.lng! }}
                title={`${call.caller_phone ?? 'Unknown'} — ${call.status ?? '—'}`}
              >
                <Pin {...p} scale={call.status === 'Active' ? 1.3 : 1.0} />
              </AdvancedMarker>
            )
          })}

          {/* Mock rescue units — placeholder until real fleet tracking exists */}
          {MOCK_UNITS.map((u, i) => (
            <AdvancedMarker
              key={`unit-${i}`}
              position={{ lat: u.lat, lng: u.lng }}
              title={`Rescue unit — ${u.kind}`}
            >
              <Pin {...UNIT_PIN[u.kind]} scale={0.8} />
            </AdvancedMarker>
          ))}
        </Map>
      </APIProvider>

      {/* Legend overlay (floats above map) */}
      <div className="absolute top-3 right-3 glass px-3 py-2.5 rounded-xl pointer-events-none">
        <p className="text-[10px] font-semibold text-slate-500 dark:text-zinc-400 mb-2 uppercase tracking-wider">Legend</p>
        <div className="space-y-1.5">
          {[
            { color: 'bg-red-500',     label: 'Emergency' },
            { color: 'bg-cyan-500',    label: 'En Route' },
            { color: 'bg-emerald-500', label: 'Available' },
            { color: 'bg-amber-500',   label: 'Standby' },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${item.color} flex-shrink-0`} />
              <span className="text-[10px] text-slate-500 dark:text-zinc-400">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom status pill */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 glass px-4 py-2 rounded-xl flex items-center gap-2 pointer-events-none">
        <MapPin className="w-3.5 h-3.5 text-teal-600 dark:text-cyan-400" />
        <p className="text-xs text-slate-700 dark:text-zinc-300 font-medium whitespace-nowrap">
          {placedCalls.length
            ? `${placedCalls.length} call${placedCalls.length !== 1 ? 's' : ''} plotted`
            : 'Live Tracking Active'}
        </p>
      </div>
    </div>
  )
}
