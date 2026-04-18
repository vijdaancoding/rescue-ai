import { useEffect, useMemo, useRef, useState } from 'react'
import Layout from '../components/Layout'
import {
  Activity, AlertTriangle, CheckCircle2, Database, Radio, Server, Wifi, WifiOff,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Line, LineChart,
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Probe {
  name: string
  ok: boolean
  latency_ms: number
  detail: string
}

interface Status {
  ok: boolean
  probes: Probe[]
  uptime_seconds: number
  version: string
}

interface EndpointStats {
  method: string
  path: string
  count_recent: number
  count_total: number
  errors_total: number
  p50_ms: number
  p95_ms: number
  p99_ms: number
  avg_ms: number
  max_ms: number
}

interface ErrorSample {
  ts: number
  method: string
  path: string
  status: number
  duration_ms: number
  request_id: string | null
}

interface Metrics {
  started_at: number
  uptime_seconds: number
  total_requests: number
  total_errors: number
  endpoints: EndpointStats[]
  recent_errors: ErrorSample[]
}

interface LiveSample {
  ts: number
  durationMs: number
  status: number
}

const METRICS_POLL_MS = 5000
const STATUS_POLL_MS = 15000
const MAX_LIVE_SAMPLES = 60
const PROBE_ICON: Record<string, React.ReactNode> = {
  database: <Database className="w-4 h-4" />,
  livekit: <Radio className="w-4 h-4" />,
  opencage: <Server className="w-4 h-4" />,
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

function StatCard({ label, value, sub, tone = 'neutral' }: {
  label: string; value: string | number; sub?: string
  tone?: 'neutral' | 'good' | 'warn' | 'bad'
}) {
  const toneColor = {
    neutral: 'text-slate-900 dark:text-zinc-100',
    good: 'text-emerald-600 dark:text-emerald-400',
    warn: 'text-amber-600 dark:text-amber-400',
    bad: 'text-red-600 dark:text-red-400',
  }[tone]
  return (
    <div className="card text-center py-5">
      <p className={`text-3xl font-bold tabular mb-1 ${toneColor}`}>{value}</p>
      <p className="text-sm font-medium text-slate-600 dark:text-zinc-400">{label}</p>
      {sub && <p className="text-xs text-slate-400 dark:text-zinc-600 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Health() {
  const { token } = useAuth()
  const { theme } = useTheme()
  const [status, setStatus] = useState<Status | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [live, setLive] = useState<LiveSample[]>([])
  const [wsConnected, setWsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Poll status + metrics.
  useEffect(() => {
    let cancelled = false
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}

    async function fetchStatus() {
      try {
        const r = await fetch(`${API_URL}/health/status`, { headers })
        if (!cancelled) setStatus(await r.json())
      } catch (e) { if (!cancelled) setError((e as Error).message) }
    }
    async function fetchMetrics() {
      try {
        const r = await fetch(`${API_URL}/health/metrics`, { headers })
        if (!cancelled) setMetrics(await r.json())
      } catch (e) { if (!cancelled) setError((e as Error).message) }
    }

    fetchStatus()
    fetchMetrics()
    const si = setInterval(fetchStatus, STATUS_POLL_MS)
    const mi = setInterval(fetchMetrics, METRICS_POLL_MS)
    return () => { cancelled = true; clearInterval(si); clearInterval(mi) }
  }, [token])

  // Live-tail WebSocket for request samples.
  useEffect(() => {
    const wsUrl = API_URL.replace(/^http/, 'ws') + '/health/ws'
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onerror = () => setWsConnected(false)
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'sample') {
          setLive(prev => {
            const next = [...prev, { ts: msg.ts, durationMs: msg.duration_ms, status: msg.status }]
            return next.length > MAX_LIVE_SAMPLES ? next.slice(-MAX_LIVE_SAMPLES) : next
          })
        }
      } catch { /* ignore malformed */ }
    }
    return () => { ws.close() }
  }, [])

  const liveChartData = useMemo(
    () => live.map((s, i) => ({ i, ms: s.durationMs, err: s.status >= 400 })),
    [live],
  )

  const slowestEndpoints = useMemo(
    () => (metrics?.endpoints ?? []).slice().sort((a, b) => b.p95_ms - a.p95_ms).slice(0, 10),
    [metrics],
  )

  const isDark = theme === 'dark'
  const tickColor = isDark ? '#52525b' : '#94a3b8'
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)'
  const tooltipStyle = isDark
    ? { backgroundColor: '#18181b', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', fontSize: '12px', color: '#e4e4e7' }
    : { backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px', color: '#0f172a' }

  if (error && !metrics && !status) {
    return (
      <Layout title="System Health">
        <div className="card text-center py-12">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        </div>
      </Layout>
    )
  }

  const errorRate = metrics && metrics.total_requests > 0
    ? (metrics.total_errors / metrics.total_requests) * 100
    : 0

  return (
    <Layout title="System Health">
      <div className="space-y-5">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-800 dark:text-zinc-200">System Health & Observability</h2>
            <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">
              Live probes, per-endpoint latency, and recent errors
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            {wsConnected
              ? <><Wifi className="w-3.5 h-3.5 text-emerald-500" /><span className="text-emerald-600 dark:text-emerald-400">Live</span></>
              : <><WifiOff className="w-3.5 h-3.5 text-slate-400" /><span className="text-slate-400 dark:text-zinc-500">Reconnecting…</span></>
            }
          </div>
        </div>

        {/* Overall status pill + top stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Overall"
            value={status ? (status.ok ? 'HEALTHY' : 'DEGRADED') : '—'}
            tone={status?.ok ? 'good' : status ? 'bad' : 'neutral'}
          />
          <StatCard
            label="Uptime"
            value={status ? formatUptime(status.uptime_seconds) : '—'}
            sub={status?.version ? `v${status.version}` : undefined}
          />
          <StatCard
            label="Total Requests"
            value={metrics?.total_requests?.toLocaleString() ?? '—'}
          />
          <StatCard
            label="Error Rate"
            value={metrics ? `${errorRate.toFixed(2)}%` : '—'}
            sub={metrics ? `${metrics.total_errors} errors` : undefined}
            tone={errorRate === 0 ? 'good' : errorRate > 5 ? 'bad' : 'warn'}
          />
        </div>

        {/* Probes */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-1">External Dependencies</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-600 mb-4">Synchronous probe on each status check</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {(status?.probes ?? []).map(p => (
              <div key={p.name} className="flex items-center gap-3 p-3.5 bg-slate-50 dark:bg-zinc-800/50 rounded-xl border border-slate-200 dark:border-zinc-800">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${p.ok ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400' : 'bg-red-100 text-red-600 dark:bg-red-500/15 dark:text-red-400'}`}>
                  {PROBE_ICON[p.name] ?? <Server className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 dark:text-zinc-200 capitalize">{p.name}</p>
                  <p className="text-xs text-slate-400 dark:text-zinc-600 truncate" title={p.detail}>
                    {p.ok ? `${p.latency_ms} ms` : (p.detail || 'Unhealthy')}
                  </p>
                </div>
                {p.ok
                  ? <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                  : <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />}
              </div>
            ))}
            {(!status || status.probes.length === 0) && (
              <p className="text-sm text-slate-400 dark:text-zinc-600 col-span-full text-center py-3">No probes configured</p>
            )}
          </div>
        </div>

        {/* Live request stream */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-1 flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-teal-500 dark:text-cyan-400" /> Live Request Latency
          </h3>
          <p className="text-xs text-slate-400 dark:text-zinc-600 mb-4">Last {MAX_LIVE_SAMPLES} requests streamed over WebSocket</p>
          {liveChartData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-slate-400 dark:text-zinc-600 text-sm">Waiting for traffic…</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={liveChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="i" tick={{ fill: tickColor, fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: tickColor, fontSize: 10 }} axisLine={false} tickLine={false} unit=" ms" />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="ms" stroke="#06b6d4" strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Per-endpoint percentiles */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-1">Slowest Endpoints (p95, 5-min window)</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-600 mb-4">Ranked by p95 latency across recent traffic</p>
          {slowestEndpoints.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-zinc-600 text-center py-6">No traffic yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(200, slowestEndpoints.length * 36)}>
              <BarChart
                data={slowestEndpoints.map(e => ({ ...e, label: `${e.method} ${e.path}` }))}
                layout="vertical"
                barSize={10}
                margin={{ left: 10, right: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} horizontal={false} />
                <XAxis type="number" tick={{ fill: tickColor, fontSize: 10 }} axisLine={false} tickLine={false} unit=" ms" />
                <YAxis
                  dataKey="label"
                  type="category"
                  tick={{ fill: isDark ? '#a1a1aa' : '#64748b', fontSize: 11 }}
                  width={240}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="p50_ms" name="p50" fill="#10b981" radius={[0, 3, 3, 0]} />
                <Bar dataKey="p95_ms" name="p95" fill="#f59e0b" radius={[0, 3, 3, 0]} />
                <Bar dataKey="p99_ms" name="p99" fill="#ef4444" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent errors */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-1">Recent Errors</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-600 mb-4">Last {metrics?.recent_errors.length ?? 0} responses with status ≥ 400</p>
          {!metrics || metrics.recent_errors.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-zinc-600 text-center py-6">No errors recorded</p>
          ) : (
            <div className="space-y-2">
              {metrics.recent_errors.slice(0, 30).map((e, idx) => {
                const d = new Date(e.ts * 1000)
                const isServerError = e.status >= 500
                return (
                  <div
                    key={`${e.ts}-${idx}`}
                    className="flex items-center gap-4 p-3 bg-slate-50 dark:bg-zinc-800/40 rounded-xl border border-slate-100 dark:border-zinc-800/50"
                  >
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full w-12 text-center ${isServerError ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400'}`}>
                      {e.status}
                    </span>
                    <span className="text-xs font-mono text-slate-700 dark:text-zinc-300 w-14">{e.method}</span>
                    <span className="text-sm font-mono text-slate-800 dark:text-zinc-200 flex-1 truncate">{e.path}</span>
                    <span className="text-xs text-slate-400 dark:text-zinc-600 tabular">{e.duration_ms.toFixed(1)} ms</span>
                    <span className="text-xs text-slate-400 dark:text-zinc-600 tabular w-20 text-right">
                      {d.toLocaleTimeString('en-GB', { hour12: false })}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <p className="text-center text-xs text-slate-300 dark:text-zinc-700 py-2">
          Observability — in-process telemetry, not a substitute for APM
        </p>
      </div>
    </Layout>
  )
}
