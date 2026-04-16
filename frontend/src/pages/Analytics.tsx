import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts'
import { TrendingUp, AlertTriangle, CheckCircle, Clock, Phone, Shield, HeartPulse, Flame, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import type { AnalyticsSummary, AnalyticsByDay, AnalyticsDispatch, CallSummary } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const URGENCY_ICON: Record<string, React.ReactNode> = {
  critical: <AlertTriangle className="w-4 h-4 text-red-500" />,
  high:     <AlertTriangle className="w-4 h-4 text-orange-500" />,
  medium:   <Clock         className="w-4 h-4 text-amber-500" />,
  low:      <CheckCircle   className="w-4 h-4 text-emerald-500" />,
}

const URGENCY_COLOR_MAP: Record<string, string> = {
  critical: 'text-red-600 dark:text-red-400',
  high:     'text-orange-600 dark:text-orange-400',
  medium:   'text-amber-600 dark:text-amber-400',
  low:      'text-emerald-600 dark:text-emerald-400',
}

const DISPATCH_ICON_MAP: Record<string, React.ReactNode> = {
  police:      <Shield    className="w-4 h-4 text-blue-500" />,
  ambulance:   <HeartPulse className="w-4 h-4 text-red-500" />,
  firefighters:<Flame     className="w-4 h-4 text-orange-500" />,
}

const DISPATCH_COLOR: Record<string, string> = {
  police: '#60a5fa', ambulance: '#f87171', firefighters: '#fb923c',
}

function StatCard({ label, value, sub, color = 'text-slate-900 dark:text-zinc-100' }: {
  label: string; value: string | number; sub?: string; color?: string
}) {
  return (
    <div className="card text-center py-5">
      <p className={`text-3xl font-bold tabular mb-1 ${color}`}>{value}</p>
      <p className="text-sm font-medium text-slate-600 dark:text-zinc-400">{label}</p>
      {sub && <p className="text-xs text-slate-400 dark:text-zinc-600 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Analytics() {
  const { token } = useAuth()
  const { theme } = useTheme()
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [byDay, setByDay] = useState<AnalyticsByDay[]>([])
  const [dispatchBreakdown, setDispatchBreakdown] = useState<AnalyticsDispatch[]>([])
  const [recentCalls, setRecentCalls] = useState<CallSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    const headers = { Authorization: `Bearer ${token}` }

    Promise.all([
      fetch(`${API_URL}/api/analytics/summary`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/api/analytics/by-day`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/api/analytics/dispatches`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/calls/?limit=5`, { headers }).then(r => r.json()),
    ])
      .then(([sum, days, dispatches, recent]) => {
        setSummary(sum); setByDay(days); setDispatchBreakdown(dispatches); setRecentCalls(recent)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) return (
    <Layout title="Analytics">
      <div className="flex items-center justify-center h-64 gap-3 text-slate-400 dark:text-zinc-600">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span className="text-sm">Loading analytics...</span>
      </div>
    </Layout>
  )

  if (error) return (
    <Layout title="Analytics">
      <div className="card text-center py-12">
        <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
      </div>
    </Layout>
  )

  const spamPct = summary && summary.total_calls > 0
    ? Math.round((summary.spam_calls / summary.total_calls) * 100) : 0

  const chartData = byDay.map(d => ({ ...d, label: d.date.slice(5) }))
  const isDark = theme === 'dark'

  const tickColor  = isDark ? '#52525b' : '#94a3b8'
  const gridColor  = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)'
  const tooltipStyle = isDark
    ? { backgroundColor: '#18181b', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', fontSize: '12px', color: '#e4e4e7' }
    : { backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px', color: '#0f172a' }
  const cursorStyle = isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.04)'

  return (
    <Layout title="Analytics">
      <div className="space-y-5">

        <div>
          <h2 className="text-base font-semibold text-slate-800 dark:text-zinc-200">Incident Analytics</h2>
          <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">Live data — call patterns, spam detection, dispatch stats</p>
        </div>

        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Calls" value={summary.total_calls} />
            <StatCard label="Real Emergencies" value={summary.real_calls} color="text-emerald-600 dark:text-emerald-400" />
            <StatCard label="Spam / Prank" value={summary.spam_calls} sub={`${spamPct}% of all calls`} color="text-red-600 dark:text-red-400" />
            <StatCard label="Dispatched" value={summary.dispatched} color="text-blue-600 dark:text-blue-400" />
          </div>
        )}

        {/* Charts */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-1">Incident Response Overview</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-600 mb-6">Last 30 days — real emergencies vs spam calls per day</p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h4 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-teal-500 dark:text-cyan-400" /> Real vs Spam by Day
              </h4>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={chartData} barSize={10}>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis dataKey="label" tick={{ fill: tickColor, fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: tickColor, fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: cursorStyle }} />
                    <Legend wrapperStyle={{ fontSize: '11px', color: tickColor }} />
                    <Bar dataKey="real" name="Real" fill="#10b981" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="spam" name="Spam" fill="#f87171" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[240px] flex items-center justify-center text-slate-400 dark:text-zinc-600 text-sm">No data for the last 30 days</div>
              )}
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Dispatch Breakdown by Service
              </h4>
              {dispatchBreakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={dispatchBreakdown} layout="vertical" barSize={18}>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} horizontal={false} />
                    <XAxis type="number" tick={{ fill: tickColor, fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="dispatch_type" type="category" tick={{ fill: isDark ? '#a1a1aa' : '#64748b', fontSize: 11 }} width={90} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: cursorStyle }} />
                    <Bar dataKey="count" name="Dispatched" radius={[0, 4, 4, 0]}>
                      {dispatchBreakdown.map(entry => (
                        <Cell key={entry.dispatch_type} fill={DISPATCH_COLOR[entry.dispatch_type] ?? '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[240px] flex items-center justify-center text-slate-400 dark:text-zinc-600 text-sm">No dispatch records yet</div>
              )}
            </div>
          </div>
        </div>

        {/* Urgency breakdown */}
        {summary && Object.keys(summary.urgency_breakdown).length > 0 && (
          <div className="card">
            <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-4">Urgency Distribution</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {(['critical', 'high', 'medium', 'low'] as const).map(level => {
                const count = summary.urgency_breakdown[level] ?? 0
                return (
                  <div key={level} className="flex items-center gap-3 p-3.5 bg-slate-50 dark:bg-zinc-800/50 rounded-xl border border-slate-200 dark:border-zinc-800">
                    {URGENCY_ICON[level]}
                    <div>
                      <p className={`font-bold text-xl tabular ${URGENCY_COLOR_MAP[level]}`}>{count}</p>
                      <p className="text-xs text-slate-400 dark:text-zinc-600 capitalize">{level}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Recent Calls */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 dark:text-zinc-500 uppercase tracking-wider mb-1">Recent Calls</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-600 mb-4">Last 5 calls</p>

          {recentCalls.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-zinc-600 text-center py-6">No calls found</p>
          ) : (
            <div className="space-y-2">
              {recentCalls.map(call => {
                const dt = call.start_time ? new Date(call.start_time) : null
                const isSpam = call.spam_label === 'spam'
                return (
                  <div key={call.id} className="flex items-center gap-4 p-3.5 bg-slate-50 dark:bg-zinc-800/40 rounded-xl border border-slate-100 dark:border-zinc-800/50">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isSpam ? 'bg-red-100 dark:bg-red-500/15' :
                      call.urgency_level === 'critical' || call.urgency_level === 'high' ? 'bg-orange-100 dark:bg-orange-500/15' :
                      'bg-teal-50 dark:bg-cyan-500/15'
                    }`}>
                      {isSpam
                        ? <Phone className="w-4 h-4 text-red-500" />
                        : (URGENCY_ICON[call.urgency_level ?? 'low'] ?? <CheckCircle className="w-4 h-4 text-teal-500 dark:text-cyan-400" />)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800 dark:text-zinc-200 truncate font-mono">
                        {call.caller_phone || 'Unknown caller'}
                        {call.caller_country ? <span className="text-slate-400 dark:text-zinc-500 font-sans"> · {call.caller_country}</span> : ''}
                      </p>
                      <p className="text-xs text-slate-400 dark:text-zinc-600">
                        {dt ? dt.toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {call.spam_label && (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isSpam ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'}`}>
                          {isSpam ? 'Spam' : 'Real'}
                        </span>
                      )}
                      {call.urgency_level && (
                        <span className={`text-xs font-semibold capitalize ${URGENCY_COLOR_MAP[call.urgency_level] ?? 'text-slate-500'}`}>
                          {call.urgency_level}
                        </span>
                      )}
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        call.status === 'Dispatched' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400' :
                        call.status === 'FalseAlarm' ? 'bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-500' :
                        'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400'
                      }`}>
                        {call.status}
                      </span>
                    </div>
                    {call.dispatch_types.length > 0 && (
                      <div className="flex gap-1 flex-shrink-0">
                        {call.dispatch_types.map(t => (<span key={t} title={t}>{DISPATCH_ICON_MAP[t]}</span>))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <p className="text-center text-xs text-slate-300 dark:text-zinc-700 py-2">
          Confidential — authorized viewing only · © 2026 Rescue AI
        </p>
      </div>
    </Layout>
  )
}
