import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LiveMap from '../components/LiveMap'
import {
  Phone, PhoneOff, Activity, Wifi, CheckCircle,
  ShieldAlert, Zap, PhoneIncoming, ArrowRight, FlaskConical,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { CallSummary } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_WS_URL = API_URL.replace(/^http/, 'ws')
const MAP_POLL_MS = 10000

interface AnalysisSummary {
  spam_score: number
  spam_label: string
  urgency_score: number
  urgency_label: string
  analysis_count: number
}

const URGENCY_PILL: Record<string, { bg: string; text: string; darkBg: string; darkText: string }> = {
  critical: { bg: 'bg-red-100', text: 'text-red-700', darkBg: 'dark:bg-red-500/15', darkText: 'dark:text-red-400' },
  high:     { bg: 'bg-orange-100', text: 'text-orange-700', darkBg: 'dark:bg-orange-500/15', darkText: 'dark:text-orange-400' },
  medium:   { bg: 'bg-amber-100', text: 'text-amber-700', darkBg: 'dark:bg-amber-500/15', darkText: 'dark:text-amber-400' },
  low:      { bg: 'bg-emerald-100', text: 'text-emerald-700', darkBg: 'dark:bg-emerald-500/15', darkText: 'dark:text-emerald-400' },
}

function urgencyBarColor(label: string): string {
  if (label === 'critical') return 'bg-red-500'
  if (label === 'high') return 'bg-orange-500'
  if (label === 'medium') return 'bg-amber-400'
  return 'bg-emerald-500'
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { token: authToken } = useAuth()
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisSummary | null>(null)
  const [mapCalls, setMapCalls] = useState<CallSummary[]>([])
  const dashboardWsRef = useRef<WebSocket | null>(null)

  // Poll for recent calls so the live map stays current.
  useEffect(() => {
    if (!authToken) return
    let cleaned = false
    const fetchCalls = async () => {
      try {
        const res = await fetch(`${API_URL}/calls/?limit=25`, {
          headers: { Authorization: `Bearer ${authToken}` },
        })
        if (!res.ok) return
        const data: CallSummary[] = await res.json()
        if (!cleaned) setMapCalls(data)
      } catch { /* ignore */ }
    }
    void fetchCalls()
    const timer = setInterval(() => { void fetchCalls() }, MAP_POLL_MS)
    return () => { cleaned = true; clearInterval(timer) }
  }, [authToken])

  // Active call derived from the live-polled mapCalls list. Defensive time bound:
  // only trust status='Active' rows that started in the last 15 minutes. Prevents
  // stale/zombie rows (from missed /twilio/status callbacks) from appearing live.
  const ACTIVE_MAX_AGE_SECONDS = 15 * 60
  const isFresh = (startIso: string | null) => {
    if (!startIso) return false
    const hasTz = /[Zz]$|[+-]\d{2}:?\d{2}$/.test(startIso)
    const startMs = new Date(hasTz ? startIso : startIso + 'Z').getTime()
    return (Date.now() - startMs) / 1000 < ACTIVE_MAX_AGE_SECONDS
  }
  const freshActive = mapCalls.filter(c => c.status === 'Active' && isFresh(c.start_time))
  const activeCall = freshActive[0] || null
  const activeCallCount = freshActive.length

  // Elapsed seconds for the active call, ticking every second.
  // Backend may serialize naive UTC datetimes without 'Z' — append it defensively
  // so the browser doesn't double-subtract the local tz offset.
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!activeCall?.start_time) { setElapsed(0); return }
    const raw = activeCall.start_time
    const hasTz = /[Zz]$|[+-]\d{2}:?\d{2}$/.test(raw)
    const startMs = new Date(hasTz ? raw : raw + 'Z').getTime()
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - startMs) / 1000)))
    tick()
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)
  }, [activeCall?.start_time])

  const formatElapsed = (s: number) => {
    const m = Math.floor(s / 60); const r = s % 60
    return `${m.toString().padStart(2, '0')}:${r.toString().padStart(2, '0')}`
  }

  useEffect(() => {
    let isCleanup = false
    const ws = new WebSocket(`${API_WS_URL}/ws/dashboard`)
    dashboardWsRef.current = ws

    ws.onmessage = (event) => {
      if (isCleanup) return
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'analysis_update') {
          // Only surface analysis that matches the *currently active* call.
          if (activeCall && data.call_id !== activeCall.id) return
          setLatestAnalysis({
            spam_score: data.spam_score,
            spam_label: data.spam_label,
            urgency_score: data.urgency_score,
            urgency_label: data.urgency_label,
            analysis_count: data.analysis_count,
          })
        }
      } catch { /* ignore */ }
    }

    return () => {
      isCleanup = true
      ws.close()
    }
  }, [activeCall?.id])

  // Clear analysis when no active call.
  useEffect(() => {
    if (!activeCall) setLatestAnalysis(null)
  }, [activeCall])

  const filteredCalls = [
    { id: 2, label: 'Prank Call #1', time: '2 min ago', spamPct: 94 },
    { id: 3, label: 'Prank Call #2', time: '5 min ago', spamPct: 88 },
    { id: 4, label: 'Prank Call #3', time: '8 min ago', spamPct: 97 },
  ]

  const isSpam = latestAnalysis?.spam_label === 'spam'
  const urgencyLabel = latestAnalysis?.urgency_label ?? 'medium'
  const urgencyPct = latestAnalysis ? Math.round(latestAnalysis.urgency_score * 100) : null
  const spamPct = latestAnalysis ? Math.round(latestAnalysis.spam_score * 100) : null
  const up = URGENCY_PILL[urgencyLabel]

  const systemStatus = [
    { label: 'Network', ok: true, icon: Wifi },
    { label: 'Database', ok: true, icon: CheckCircle },
    { label: 'WebSocket', ok: true, icon: Activity },
    { label: 'AI Pipeline', ok: !!latestAnalysis, live: !!latestAnalysis, icon: Zap },
  ]

  return (
    <Layout title="Live View">
      <div className="space-y-5">

        {/* Status bar */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-1.5 border rounded-lg ${
              activeCallCount > 0
                ? 'bg-red-50 border-red-200 dark:bg-red-500/10 dark:border-red-500/25'
                : 'bg-slate-50 border-slate-200 dark:bg-zinc-800/40 dark:border-zinc-700/50'
            }`}>
              <div className={`w-2 h-2 rounded-full ${activeCallCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-slate-400 dark:bg-zinc-600'}`} />
              <span className={`text-xs font-semibold ${activeCallCount > 0 ? 'text-red-700 dark:text-red-400' : 'text-slate-500 dark:text-zinc-500'}`}>
                {activeCallCount > 0 ? `${activeCallCount} Active Call${activeCallCount > 1 ? 's' : ''}` : 'No Active Calls'}
              </span>
            </div>
            {latestAnalysis && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-cyan-50 border border-cyan-200 dark:bg-cyan-500/10 dark:border-cyan-500/25 rounded-lg">
                <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
                <span className="text-xs font-semibold text-cyan-700 dark:text-cyan-400">AI Active</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {systemStatus.map(s => {
              const Icon = s.icon
              return (
                <div key={s.label} className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 dark:bg-zinc-800/50 rounded-lg">
                  <Icon className={`w-3 h-3 ${s.live ? 'text-cyan-500' : s.ok ? 'text-emerald-500' : 'text-red-500'}`} />
                  <span className="text-[10px] font-medium text-slate-500 dark:text-zinc-500">{s.label}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,420px)_1fr] gap-5">

          {/* LEFT: Call Queue */}
          <div className="flex flex-col gap-4">

            {/* Active call — prominent */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <PhoneIncoming className={`w-3.5 h-3.5 ${activeCall ? 'text-red-500' : 'text-slate-400 dark:text-zinc-600'}`} />
                <p className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
                  {activeCall ? 'Active Call' : 'Incoming'}
                </p>
                {activeCallCount > 0 && (
                  <span className="badge badge-danger px-1.5 py-0.5 text-[10px] ml-auto">{activeCallCount}</span>
                )}
              </div>

              {!activeCall && (
                <div className="rounded-2xl border border-dashed border-slate-200 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-900/30 p-6 text-center">
                  <div className="w-10 h-10 mx-auto mb-2 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center">
                    <Phone className="w-4 h-4 text-slate-400 dark:text-zinc-600" />
                  </div>
                  <p className="text-sm font-medium text-slate-500 dark:text-zinc-500">No active call right now</p>
                  <p className="text-xs text-slate-400 dark:text-zinc-600 mt-1">Waiting for incoming emergency</p>
                  <button
                    onClick={() => navigate('/test-call')}
                    className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                      bg-white border border-slate-200 text-slate-600 hover:border-amber-300 hover:text-amber-700
                      dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-400 dark:hover:border-amber-500/40 dark:hover:text-amber-400
                      transition-colors"
                  >
                    <FlaskConical className="w-3.5 h-3.5" />
                    Browser test call
                  </button>
                </div>
              )}

              {activeCall && (
              <div
                onClick={() => navigate(`/live/${activeCall.id}`)}
                className="cursor-pointer rounded-2xl border-2 border-red-300 dark:border-red-500/40 bg-red-50 dark:bg-red-500/[0.06] hover:border-red-400 dark:hover:border-red-500/60 transition-all duration-200 overflow-hidden"
              >
                {/* Card top */}
                <div className="px-5 pt-5 pb-4">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="relative w-11 h-11 flex-shrink-0">
                        <div className="w-11 h-11 bg-red-100 dark:bg-red-500/20 rounded-xl flex items-center justify-center">
                          <Phone className="w-5 h-5 text-red-600 dark:text-red-400" />
                        </div>
                        <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 rounded-full border-2 border-white dark:border-zinc-900 animate-pulse" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900 dark:text-zinc-100 font-mono">
                          {activeCall.caller_phone || 'Unknown'}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-zinc-500 mt-0.5">
                          Ongoing · <span className="tabular font-medium">{formatElapsed(elapsed)}</span>
                          {(activeCall.caller_city || activeCall.caller_country) && (
                            <> · {[activeCall.caller_city, activeCall.caller_country].filter(Boolean).join(', ')}</>
                          )}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold tracking-wider text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                      LIVE
                    </span>
                  </div>

                  {/* AI Analysis — shown when available */}
                  {latestAnalysis ? (
                    <div className="space-y-2.5 mb-4">
                      {/* Spam bar */}
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <div className="flex items-center gap-1.5">
                            <ShieldAlert className="w-3 h-3 text-slate-400 dark:text-zinc-500" />
                            <span className="text-[10px] font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wide">Spam</span>
                          </div>
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            isSpam
                              ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400'
                              : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'
                          }`}>
                            {isSpam ? 'SPAM' : 'REAL'} · {spamPct}%
                          </span>
                        </div>
                        <div className="h-1.5 rounded-full bg-slate-200 dark:bg-zinc-700 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-1000 ${isSpam ? 'bg-red-500' : 'bg-emerald-500'}`}
                            style={{ width: `${spamPct}%` }}
                          />
                        </div>
                      </div>
                      {/* Urgency bar */}
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <div className="flex items-center gap-1.5">
                            <Zap className="w-3 h-3 text-slate-400 dark:text-zinc-500" />
                            <span className="text-[10px] font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wide">Urgency</span>
                          </div>
                          {up && (
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${up.bg} ${up.text} ${up.darkBg} ${up.darkText}`}>
                              {urgencyLabel.toUpperCase()} · {urgencyPct}%
                            </span>
                          )}
                        </div>
                        <div className="h-1.5 rounded-full bg-slate-200 dark:bg-zinc-700 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-1000 ${urgencyBarColor(urgencyLabel)}`}
                            style={{ width: `${urgencyPct ?? 34}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 mb-4 py-2.5 px-3 bg-white/60 dark:bg-zinc-900/40 rounded-lg border border-slate-200/80 dark:border-zinc-700/40">
                      <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                      <p className="text-xs text-slate-500 dark:text-zinc-500">AI analysis pending...</p>
                    </div>
                  )}

                  {/* Listen Live button — Twilio auto-answers, so dispatcher observes */}
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/live/${activeCall.id}`) }}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-red-600 hover:bg-red-500 active:scale-[0.99] text-white rounded-xl font-semibold text-sm transition-all duration-150 shadow-lg shadow-red-500/20"
                  >
                    <PhoneIncoming className="w-4 h-4" />
                    Listen Live
                    <ArrowRight className="w-4 h-4 ml-auto" />
                  </button>
                </div>
              </div>
              )}
            </div>

            {/* Filtered / blocked calls */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <PhoneOff className="w-3.5 h-3.5 text-slate-400 dark:text-zinc-600" />
                <p className="text-xs font-semibold text-slate-400 dark:text-zinc-600 uppercase tracking-widest">Filtered Out</p>
                <span className="ml-auto text-[10px] font-semibold text-slate-400 dark:text-zinc-600">{filteredCalls.length}</span>
              </div>
              <div className="space-y-1.5">
                {filteredCalls.map(call => (
                  <div
                    key={call.id}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-100/80 dark:bg-zinc-800/40 border border-slate-200 dark:border-zinc-800"
                  >
                    <div className="w-7 h-7 bg-slate-200 dark:bg-zinc-700 rounded-lg flex items-center justify-center flex-shrink-0">
                      <PhoneOff className="w-3.5 h-3.5 text-slate-400 dark:text-zinc-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-slate-500 dark:text-zinc-500 truncate">{call.label}</p>
                      <p className="text-[10px] text-slate-400 dark:text-zinc-600">{call.time}</p>
                    </div>
                    <span className="text-[10px] font-semibold text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-1.5 py-0.5 rounded flex-shrink-0">
                      SPAM {call.spamPct}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* System status row */}
            <div className="mt-auto pt-2">
              <p className="text-[10px] font-semibold text-slate-400 dark:text-zinc-600 uppercase tracking-widest mb-2">System</p>
              <div className="grid grid-cols-2 gap-1.5">
                {systemStatus.map(s => {
                  const Icon = s.icon
                  return (
                    <div key={s.label} className="flex items-center gap-2 px-3 py-2 bg-slate-100 dark:bg-zinc-800/50 rounded-lg">
                      <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${s.live ? 'text-cyan-500' : s.ok ? 'text-emerald-500' : 'text-red-500'}`} />
                      <span className="text-[11px] text-slate-600 dark:text-zinc-400 flex-1">{s.label}</span>
                      <span className={`text-[10px] font-bold ${s.live ? 'text-cyan-500' : s.ok ? 'text-emerald-500' : 'text-red-500'}`}>
                        {s.live ? 'LIVE' : s.ok ? 'OK' : 'ERR'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* RIGHT: Live Map */}
          <div className="card flex flex-col" style={{ minHeight: '540px' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">Live Map</h2>
              <span className="badge badge-info text-[10px]">
                {mapCalls.filter(c => c.lat != null && c.lng != null).length} pins · 3 units
              </span>
            </div>
            <LiveMap calls={mapCalls} />
          </div>
        </div>
      </div>
    </Layout>
  )
}
